"""
``portfolio`` module contains basic definitions for positions and composite positions (portfolio)
on Uniswap V3
"""

from typing import List, Optional, Tuple
import numpy as np
from strategy.uni import align_for_liquidity, liq, xy


class AbstractPosition:
    """
    ``AbstractPosition`` is a abstract class for Position and Portfolio classes
    :param id: Unique string id for the position
    """

    def __init__(self, id: str) -> None:
        self._id = id

    @property
    def id(self) -> str:
        return self._id

    @property
    def fees0(self) -> float:
        raise Exception(NotImplemented)

    @property
    def fees1(self) -> float:
        raise Exception(NotImplemented)

    @property
    def a(self) -> float:
        raise Exception(NotImplemented)

    @property
    def b(self) -> float:
        raise Exception(NotImplemented)

    @property
    def bi_xy(self) -> Tuple[float, float]:
        raise Exception(NotImplemented)

    @property
    def l(self) -> float:
        raise Exception(NotImplemented)

    def fees(self, c: float) -> float:
        raise Exception(NotImplemented)

    def charge_fees(self, before_c: float, after_c: float, fee_percent: float) -> Tuple[float, float]:
        raise Exception(NotImplemented)

    def reinvest_fees(self, c: float, fee_percent: float) -> float:
        raise Exception(NotImplemented)

    def deposit(self, c: float, x: float, y: float, fee_percent: float) -> float:
        raise Exception(NotImplemented)

    def rebalance(self, a: float, b: float, c: float, fee_percent: float) -> float:
        raise Exception(NotImplemented)

    def withdraw(self, c: float, l: float) -> Tuple[float, float]:
        raise Exception(NotImplemented)

    def y(self, c: float) -> float:
        raise Exception(NotImplemented)

    def xy(self, c: float) -> Tuple[float, float]:
        raise Exception(NotImplemented)

    def il(self, c: float) -> float:
        raise Exception(NotImplemented)

    def active_l(self, c: float) -> float:
        raise Exception(NotImplemented)


class Position(AbstractPosition):
    """
    ``Position`` is a primitive corresponding to one investment into UniV3 interval.
    It's defined by lower and upper bounds ``a`` and ``b``, current invested virtual liquidity ``l``
    and accumulated ``fees``.

    :param id: Unique string id for the position
    :param a: Left bound of the interval (price)
    :param b: Right bound of the interval (price)
    """

    def __init__(self, id: str, a: float, b: float):
        super().__init__(id)
        self._a = a
        self._b = b
        self._l = 0
        self._bi_y = 0
        self._bi_x = 0
        self._fees0 = 0
        self._fees1 = 0

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
            self, before_c: float, after_c: float, fee_percent: float
    ) -> Tuple[float, float]:
        """
        Takes a price movement for a specific swap and adjusts the fees account

        :param before_c: Price before the swap
        :param after_c: Price after the swap
        :param fee_percent: Fee for the current pool, e.g. 0.003

        :return: tuple of fees for ``X`` and ``Y`` tokens
        """
        c0 = min(max(self._a, before_c), self._b)
        c1 = min(max(self._a, after_c), self._b)
        x_before, y_before = self.xy(c0)
        x_after, y_after = self.xy(c1)
        fee0, fee1 = 0, 0
        if y_after <= y_before:
            fee1 = (y_before - y_after) * fee_percent
        else:
            fee0 = (x_before - x_after) * fee_percent
        self._fees0 += fee0
        self._fees1 += fee1
        return fee0, fee1

    def reinvest_fees(self, c: float, fee_percent: float) -> float:
        """
        Put accumulated fees into position

        :param c: Current price
        :param fee_percent: Fee for the current pool, e.g. 0.003

        :return: Increase of the liquidity after reinvestment
        """
        res = self.deposit(c, self.fees0, self.fees1, fee_percent)
        self._fees0 = 0
        self._fees1 = 0
        return res

    def deposit(self, c: float, x: float, y: float, fee_percent: float) -> float:
        """
        Adds ``x`` and ``y`` tokens to position.
        :param c: Current price
        :param x: Amount of ``X`` token
        :param y: Amount of ``Y`` token
        :param fee_percent: Fee for the current pool, e.g. 0.003
        :return: Liquidity added
        """
        x_c, y_c = align_for_liquidity(x, y, self._a, self._b, c, fee_percent)
        delta_l = liq(x_c, y_c, self._a, self._b, c)
        self._l += delta_l
        if self._bi_x == 0 and self._bi_y == 0:
            self._bi_x = x_c
            self._bi_y = y_c
        return delta_l

    def withdraw(self, c: float, l: float) -> Tuple[float, float]:
        """
        Withdraws ``l`` liquidity from the position. UniV3 returns ``X`` and ``Y`` tokens and all ``X`` tokens
        are converted to ``Y`` tokens at current price with no slippage.
        :param c: Current price
        :param l: Amount of liquidity to withdraw
        :return: amount of ``Y`` token actually withdrawn
        """
        x, y = xy(l, self._a, self._b, c)
        self._l -= l
        return x, y

    def y(self, c: float) -> float:
        """
        The value of the current position denominated in ``Y`` token. Doesn't include fees collected.
        :param c: Current price
        :return: amount of ``Y`` token if the position is fully withdrawn and ``X`` token converted to ``Y`` at price `c`.
        """
        x, y = self.xy(c)
        return x * c + y

    def xy(self, c: float) -> Tuple[float, float]:
        """
        Values of x and y tokens corresponding to current liquidity at price
        :param c: Current price
        :return: amount of ``X`` and ``Y`` tokens if the position is fully withdrawn
        """
        return xy(self._l, self._a, self._b, c)

    @property
    def bi_xy(self) -> Tuple[float, float]:
        return self._bi_x, self._bi_y

    @property
    def l(self) -> float:
        """
        :return: Current liquidity
        """
        return self._l

    @property
    def a(self) -> float:
        """
        :return: Left bound of the price interval
        """
        return self._a

    def rebalance(self, a: float, b: float, c: float, fee_percent: float) -> float:
        """
        Puts all liquidity into new interval
        :param a: New Left price bound value
        :param b: New Right price bound value
        :param c: Current price
        :param fee_percent: Fee for the current pool, e.g. 0.003
        :returns: Liquidity after rebalance
        """
        x, y = self.withdraw(c, self._l)
        self._a = a
        self._b = b
        return self.deposit(c, x, y, fee_percent)

    @property
    def b(self) -> float:
        """
        :return: Right bound of the price interval
        """
        return self._b

    def active_l(self, c: float) -> float:
        """
        The amount of currently active liquidity
        :param c: Current price
        :return: The amount of liquidity or 0 if price is out of (a, b) bounds
        """
        if self._a <= c <= self._b:
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

    def __repr__(self):
        return f"Position (a: {self._a}, b: {self._b}, l: {self._l}, f0: {self._fees0}, f1: {self._fees1})"


class Portfolio(AbstractPosition):
    """
    ``Portfolio`` is a container for several open positions.
    It also conforms to ``Position`` interface, aggregating all positions values.
    Note that children positions of ``Portfolio`` can also be other ``Portfolio`` objects.

    :param id: Id of the portfolio
    :param positions: List of initial positions
    """

    def __init__(self, id: str = "Portfolio", positions: List[Position] = None):
        super().__init__(id)
        if positions is None:
            positions = []
        self._positions = {pos.id: pos for pos in positions}

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
        return list(self._positions.values())

    def position(self, id: str) -> Optional[Position]:
        """
        A position with specified ``id``
        :param id: Id of the position
        :returns: A position with that id. None if id not found.
        """
        if id not in self._positions:
            return None
        return self._positions[id]

    @property
    def position_ids(self) -> List[str]:
        """
        :return: Ids of all positions in portfolio
        """
        return list(self._positions.keys())

    @property
    def fees0(self) -> float:
        """
        :return: Accumulated fees for the position for the ``X`` token
        """
        res = float(0)
        for pos in self.positions:
            res += pos.fees0
        return res

    @property
    def fees1(self) -> float:
        """
        :return: Accumulated fees for the position for the ``Y`` token
        """
        res = float(0)
        for pos in self.positions:
            res += pos.fees1
        return res

    def fees(self, c: float) -> float:
        """
        :param c: Current price
        :return: Total fees measured in ``Y`` token
        """
        res = float(0)
        for pos in self.positions:
            res += pos.fees(c)
        return res

    def charge_fees(
            self, before_c: float, after_c: float, fee_percent: float
    ) -> Tuple[float, float]:
        """
        :param before_c: Price before the swap
        :param after_c: Price after the swap
        :param fee_percent: Fee for the current pool, e.g. 0.003
        :return: tuple of fees for ``X`` and ``Y`` tokens
        """
        f0, f1 = 0, 0
        for pos in self.positions:
            fd0, fd1 = pos.charge_fees(before_c, after_c, fee_percent)
            f0 += fd0
            f1 += fd1
        return f0, f1

    def reinvest_fees(self, c: float, fee_percent: float) -> float:
        """
        :param c: Current price
        :param fee_percent: Fee for the current pool, e.g. 0.003
        :return: Accumulated increase of the liquidity after reinvestment
        """
        res = float(0)
        for pos in self.positions:
            res += pos.reinvest_fees(c, fee_percent)
        return res

    def deposit(self, c: float, x: float, y: float, fee_percent: float) -> float:
        """
        Adds ``x`` and ``y`` tokens to portfolio
        :param c: Current price
        :param x: Amount of ``X`` token
        :param y: Amount of ``Y`` token
        :param fee_percent: Fee for the current pool, e.g. 0.003
        :return: Liquidity added
        """
        res = float(0)
        total_y = self.y(c)
        for pos in self.positions:
            res += pos.deposit(c, x, pos.y(c) / total_y * y, fee_percent)
        return res

    def withdraw(self, c: float, l: float) -> float:
        """
        :param c: Current price
        :param l: Amount of liquidity to withdraw
        :return: Accumulated amount of ``Y`` token actually withdrawn
        """
        res = float(0)
        total_l = self.l
        for pos in self.positions:
            res += pos.withdraw(c, pos.l / total_l * l)
        return res

    def y(self, c: float) -> float:
        """
        :param c: Current price
        :return: Accumulated amount of ``Y`` token if the position is fully withdrawn and ``X``
        token converted to ``Y`` at price `c`.
        """
        res = float(0)
        for pos in self.positions:
            res += pos.y(c)
        return res

    def xy(self, c: float) -> Tuple[float, float]:
        """
        :param c: Current price
        :return: Accumulated amount of ``X`` and ``Y`` tokens if the position is fully withdrawn
        """
        x, y = 0, 0
        for pos in self.positions:
            xc, yc = pos.xy(c)
            x += xc
            y += yc
        return x, y

    @property
    def bi_xy(self) -> Tuple[float, float]:
        x, y = 0, 0
        for pos in self.positions:
            xc, yc = pos.bi_xy
            x += xc
            y += yc
        return x, y

    def il(self, c: float) -> float:
        """
        :param c: Current price
        :return: Accumulated amount of current impermanent loss
        """
        res = float(0)
        for pos in self.positions:
            res += pos.il(c)
        return res

    @property
    def a(self) -> float:
        """
        :return: min bound of left interval
        """
        res = np.infty
        for pos in self.positions:
            res = min(res, pos.a)
        return res

    @property
    def b(self) -> float:
        """
        :return: max bound of right interval
        """
        res = float(0)
        for pos in self.positions:
            res = max(res, pos.b)
        return res

    @property
    def l(self) -> float:
        """
        :return: Accumulated liquidity
        """
        res = float(0)
        for pos in self.positions:
            res += pos.l
        return res

    def active_l(self, c: float) -> float:
        """
        :param c: Current price
        :return: Accumulated amount of liquidity or 0 if price is out of (a, b) bounds
        """
        res = float(0)
        for pos in self.positions:
            res += pos.active_l(c)
        return res
