"""
``portfolio`` module contains basic definitions for positions and composite positions (portfolio)
on Uniswap V3

"""

from datetime import datetime
from strategy.data import PoolData
from typing import Callable, List, Optional, Tuple
import numpy as np
import pandas as pd
from strategy.uni import y_per_l


class Position:
    """
    ``Position`` is a primitive corresponding to one investment into UniV3 interval.
    It's defined by lower and upper bounds ``a`` and ``b``, current invested virtual liquidity ``l``
    and accumulated ``fees``.

    :param id: Unique string id for the position
    :param a: Left bound of the interval (price)
    :param b: Right bound of the interval (price)
    """

    def __init__(self, id: str, a: float, b: float):
        self._id = id
        self._a = a
        self._b = b
        self._l = 0
        self._bi_y = 0
        self._bi_x = 0
        self._fees0 = 0
        self._fees1 = 0

    @property
    def id(self) -> str:
        """
        Unique id of the position
        """
        return self._id

    @property
    def fees0(self) -> float:
        """
        Accumulated fees for the position for the ``X`` token
        """
        return self._fees0

    @property
    def fees1(self) -> float:
        """
        Accumulated fees for the position for the ``Y`` token
        """
        return self._fees1

    def fees(self, c: float) -> float:
        """
        Accumulated fees for the position for the ``X`` and ``Y`` token converted to ``Y`` at price ``c``.

        :param c: Current price
        :return: Total fees measured in ``Y`` token
        """

        return self._fees0 * c + self._fees1

    def charge_fees(
        self, before_c: float, after_c: float, fee_factor: float
    ) -> Tuple[float, float]:
        """
        Takes a price movement for a specific swap and adjusts the fees account

        :param before_c: Price before the swap
        :param after_c: Price after the swap
        :param fee_factor: Fee for the current pool, e.g. 0.3%

        :return: tuple of fees for ``X`` and ``Y`` tokens
        """
        x_before, y_before = self.xy(before_c)
        x_after, y_after = self.xy(after_c)
        fee0, fee1 = 0, 0
        if y_after <= y_before:
            fee1 = (y_before - y_after) * fee_factor
        else:
            fee0 = (x_before - x_after) * fee_factor
        self._fees0 += fee0
        self._fees1 += fee1
        return fee0, fee1

    def reinvest_fees(self, c: float) -> float:
        """
        Put accumulated fees into position

        :param c: Current price

        :return: Increase of the liquidity after reinvestment
        """

        res = self.deposit(c, self.fees(c))
        self._fees0 = 0
        self._fees1 = 0
        return res

    def deposit(self, c: float, y: float) -> float:
        """
        Adds ``y`` tokens to position. Tokens are assumed to be converted to token ``X``
        so that ``x`` / ``y`` ratio is optimal with no slippage and invested into uniV3 pool

        :param c: Current price
        :param y: Amount of ``Y`` token
        :return: Liquidity added
        """

        delta_l = y / y_per_l(self._a, self._b, c)
        self._l += delta_l
        self._bi_x += y / c / 2
        self._bi_y += y / 2
        return delta_l

    def withdraw(self, c: float, l: float) -> float:
        """
        Withdraws ``l`` liquidity from the position. UniV3 returns ``X`` and ``Y`` tokens and all ``X`` tokens
        are converted to ``Y`` tokens at current price with no slippage.

        :param c: Current price
        :param l: Amount of liquidity to withdraw
        :return: amount of ``Y`` token actually withdrawn
        """
        self._l -= l
        delta_y = l * y_per_l(self._a, self._b, c)
        self._bi_x -= delta_y / c / 2
        self._bi_y -= delta_y / 2
        return delta_y

    def withdraw_y(self, c: float, y: float) -> float:
        """
        Withdraws the equivalent of ``y`` tokens from the pool.

        :param c: Current price
        :param y: Amount of y token to withdraw
        :return: amount of ``Y`` token actually withdrawn
        """
        y = min(y, self.y(c))
        share = y / self.y(c)
        share = min(share, 1)
        self.withdraw(c, self.l * share)
        return y

    def y(self, c: float) -> float:
        """
        The value of the current position denominated in ``Y`` token. Doesn't include fees collected.

        :param c: Current price
        :return: amount of ``Y`` token if the position is fully withdrawn and ``X`` token converted to ``Y`` at price `c`.
        """

        return self._l * y_per_l(self._a, self._b, c)

    def xy(self, c: float) -> Tuple[float, float]:
        """
        Values of x and y tokens corresponding to current liquidity at price

        :param c: Current price
        :return: amount of ``X`` and ``Y`` tokens if the position is fully withdrawn
        """
        x, y = 0, 0
        if c > self.a:
            y = self.l * (np.sqrt(c) - np.sqrt(self.a))
        if c < self.b:
            x = self.l * (np.sqrt(self.b) - np.sqrt(c)) / np.sqrt(self.b * c)
        return x, y

    @property
    def l(self) -> float:
        """
        Current liquidity
        """
        return self._l

    @property
    def a(self) -> float:
        """
        Left bound of the price interval
        """
        return self._a

    def set_a(self, new_a: float, c: float):
        """
        Sets the new left interval bound. The position is fully withdrawn and then deposited into the new interval.

        :param new_a: New Left price bound value
        :param c: Current price
        """
        y = self.withdraw(c, self._l)
        self._a = new_a
        self.deposit(c, y)

    @property
    def b(self) -> float:
        """
        Right bound of the price interval
        """

        return self._b

    def set_b(self, new_b: float, c: float):
        """
        Sets the new right interval bound. The position is fully withdrawn and then deposited into the new interval.

        :param new_a: New right price bound value
        :param c: Current price
        """

        y = self.withdraw(c, self._l)
        self._b = new_b
        self.deposit(c, y)

    def active_l(self, c: float) -> float:
        """
        The amount of currently active liquidity

        :param c: Current price
        :return: The amount of liquidity or 0 if price is out of (a, b) bounds
        """
        if c <= self._b and c >= self._a:
            return self._l
        return float(0)

    def il(self, c: float) -> float:
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

    @property
    def id(self):
        """
        Id of the portfolio
        """
        return self._id

    def add_position(self, position: Position):
        """
        Adds position to portfolio

        :param position: Position to add
        """
        self._positions[position.id] = position

    def remove_position(self, position_id: str):
        """
        Removes a position from portfolio

        :param position_id: Id of the position to remove
        """
        del self._positions[position_id]

    @property
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

    @property
    def position_ids(self) -> List[str]:
        """
        Ids of all positions in portfolio
        """
        return self._positions.keys()

    @property
    def fees0(self) -> float:
        res = float(0)
        [res := res + pos.fees0 for pos in self.positions]
        return res

    @property
    def fees1(self) -> float:
        res = float(0)
        [res := res + pos.fees1 for pos in self.positions]
        return res

    def fees(self, c: float) -> float:
        res = float(0)
        [res := res + pos.fees(c) for pos in self.positions]
        return res

    def charge_fees(
        self, before_c: float, after_c: float, fee_factor: float
    ) -> Tuple[float, float]:
        f0, f1 = 0, 0
        for pos in self.positions:
            fd0, fd1 = pos.charge_fees(before_c, after_c, fee_factor)
            f0 += fd0
            f1 += fd1
        return f0, f1

    def reinvest_fees(self, c: float) -> float:
        res = float(0)
        [res := res + pos.reinvest_fees(c) for pos in self.positions]
        return res

    def deposit(self, с: float, y: float) -> float:
        res = float(0)
        total_y = self.y(с)
        for pos in self.positions:
            res += pos.deposit(с, pos.y(с) / total_y * y)
        return res

    def withdraw(self, с: float, l: float) -> float:
        res = float(0)
        total_l = self.l
        for pos in self.positions:
            res += pos.withdraw(с, pos.l / total_l * l)
        return res

    def withdraw_y(self, c: float, y: float) -> float:
        res = float(0)
        total_y = self.y(c)
        y = min(y, total_y)
        for pos in self.positions:
            res += pos.withdraw(c, pos.y(c) / total_y * y)
        return res

    def y(self, с: float) -> float:
        res = float(0)
        [res := res + pos.y(с) for pos in self.positions]
        return res

    def xy(self, c: float) -> Tuple[float, float]:
        x, y = 0, 0
        for pos in self.positions:
            xc, yc = pos.xy(c)
            x += xc
            y += yc
        return x, y

    def il(self, с: float) -> float:
        res = float(0)
        [res := res + pos.il(с) for pos in self.positions]
        return res

    @property
    def a(self) -> float:
        res = np.infty
        [res := min(res, pos.a) for pos in self.positions]
        return res

    @property
    def b(self) -> float:
        res = float(0)
        [res := max(res, pos.b) for pos in self.positions]
        return res

    @property
    def l(self) -> float:
        res = float(0)
        [res := res + pos.l for pos in self.positions]
        return res

    def active_l(self, c: float) -> float:
        res = float(0)
        [res := res + pos.active_l(c) for pos in self.positions]
        return res
