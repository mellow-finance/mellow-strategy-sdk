"""
``portfolio`` module contains basic definitions for positions and composite positions (portfolio)
on Uniswap V3

"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import numpy as np
import pandas as pd
from strategy.uni import y_per_l


class Position:
    """
    ``Position`` is a primitive corresponding to one investment into UniV3 interval.

    :param id: Unique string id for the position
    :param a: Left bound of the interval (price)
    :param b: Right bound of the interval (price)
    """

    def __init__(self, id: str, a: Decimal, b: Decimal):
        self._id = id
        self._a = a
        self._b = b
        self._l = Decimal(0)
        self._bi_y = Decimal(0)
        self._bi_x = Decimal(0)

    def id(self) -> str:
        return self._id

    def deposit(self, c: Decimal, y: Decimal) -> Decimal:
        """
        Adds ``y`` tokens to position. Tokens are assumed to be converted to token ``X``
        so that ``x`` / ``y`` ratio is optimal with no slippage and invested into uniV3 pool

        :param c: Current price
        :param y: Amount of ``Y`` token
        :return: Liquidity added
        """

        delta_l = y / y_per_l(self._a, self._b, c)
        self._l += delta_l
        self._bi_x += y / c / Decimal(2)
        self._bi_y += y / Decimal(2)
        return delta_l

    def withdraw(self, c: Decimal, l: Decimal) -> Decimal:
        """
        Withdraws ``l`` liquidity from the position. UniV3 returns ``X`` and ``Y`` tokens and all ``X`` tokens
        are converted to ``Y`` tokens at current price with no slippage.

        :param c: Current price
        :param l: Amount of liquidity to withdraw
        :return: amount of ``Y`` token after withdrawal
        """
        self._l -= l
        delta_y = l * y_per_l(self._a, self._b, c)
        self._bi_x -= delta_y / c / 2
        self._bi_y -= delta_y / 2
        return delta_y

    def y(self, c: Decimal) -> Decimal:
        """
        The value of the current position denominated in ``Y`` token. Doesn't include fees collected.

        :param c: Current price
        :return: amount of ``Y`` token if the position is fully withdrawn
        """

        return self._l * y_per_l(self._a, self._b, c)

    def l(self) -> Decimal:
        """
        Current liquidity
        """
        return self._l

    def a(self) -> Decimal:
        """
        Left bound of the price interval
        """
        return self._a

    def set_a(self, new_a: Decimal, c: Decimal):
        """
        Sets the new left interval bound. The position is fully withdrawn and then deposited into the new interval.

        :param new_a: New Left price bound value
        :param c: Current price
        """
        y = self.withdraw(c, self._l)
        self._a = new_a
        self.deposit(c, y)

    def b(self) -> Decimal:
        """
        Right bound of the price interval
        """

        return self._b

    def set_b(self, new_b: Decimal, c: Decimal):
        """
        Sets the new right interval bound. The position is fully withdrawn and then deposited into the new interval.

        :param new_a: New right price bound value
        :param c: Current price
        """

        y = self.withdraw(c, self._l)
        self._b = new_b
        self.deposit(c, y)

    def active_l(self, c: Decimal) -> Decimal:
        """
        The amount of currently active liquidity

        :param c: Current price
        :return: The amount of liquidity or 0 if price is out of (a, b) bounds
        """
        if c <= self._b and c >= self._a:
            return self._l
        return Decimal(0)

    def il(self, c: Decimal) -> Decimal:
        """
        The amount of current impermanent loss

        :param c: Current price
        :return: The amount of current impermanent loss
        """
        bicurrency_payoff = self._bi_x * c + self._bi_y
        return bicurrency_payoff - self.y(c)

    def __str__(self):
        return f"(a: {self._a}, b: {self._b}, l: {self._l})"


class Portfolio(Position):
    """
    ``Portfolio`` is a container for several open positions.
    It also conforms to ``Position`` interface, aggregating all positions values.
    Note that children positions of ``Portfolio`` can also be other ``Portfolio`` objects.
    """

    def __init__(self, id: str = "Portfolio", positions: List[Position] = []):
        self._positions = {pos.id: pos for pos in positions}
        self._id = id

    def id(self):
        return self._id

    def add_position(self, position: Position):
        """
        Adds position to portfolio

        :param position: Position to add
        """
        self._positions[position.id()] = position

    def remove_position(self, position_id: str):
        """
        Removes a position from portfolio

        :param position_id: Id of the position to remove
        """
        del self._positions[position_id]

    def positions(self) -> List[Position]:
        """
        A set of all open positions

        :return: a list of open positions.
        """
        return self._positions.values()

    def position(self, id: str) -> Optional[Position]:
        """
        A position with specified ``id``

        :param id: Id of the position
        :returns: A position with that id. None if id not found.
        """
        if not id in self._positions:
            return None
        return self._positions[id]

    def position_ids(self) -> List[str]:
        return self._positions.keys()

    def deposit(self, с: Decimal, y: Decimal) -> Decimal:
        res = Decimal(0)
        total_y = self.y(с)
        for pos in self.positions():
            res += pos.deposit(с, pos.y(с) / total_y * y)
        return res

    def withdraw(self, с: Decimal, l: Decimal) -> Decimal:
        res = Decimal(0)
        total_l = self.l()
        for pos in self.positions():
            res += pos.withdraw(с, pos.l() / total_l * l)
        return res

    def y(self, с: Decimal) -> Decimal:
        res = Decimal(0)
        [res := res + pos.y(с) for pos in self.positions()]
        return res

    def il(self, с: Decimal) -> Decimal:
        res = Decimal(0)
        [res := res + pos.il(с) for pos in self.positions()]
        return res

    def a(self) -> Decimal:
        res = np.infty
        [res := min(res, pos.a()) for pos in self.positions()]
        return res

    def b(self) -> Decimal:
        res = Decimal(0)
        [res := max(res, pos.b()) for pos in self.positions()]
        return res

    def l(self) -> Decimal:
        res = Decimal(0)
        [res := res + pos.l() for pos in self.positions()]
        return res

    def active_l(self, c: Decimal) -> Decimal:
        res = Decimal(0)
        [res := res + pos.active_l(c) for pos in self.positions()]
        return res


class AbstractStrategy:
    def __init__(self):
        self._portfolio = Portfolio()

    def rebalance(
        self, t: datetime, prices: pd.Series, fees0: pd.Series, fees1: pd.Series
    ):
        raise NotImplemented

    def portfolio(self):
        return self._portfolio
