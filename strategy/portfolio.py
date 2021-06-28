"""
``portfolio`` module contains basic definitions for positions and composite positions (portfolio)
on Uniswap V3

class Position
~~~~~~~~~~~~~~
.. autoclass:: Position
    :members:
"""

from strategy.uni import y_per_l


class Position:
    """
    ``Position`` is a primitive corresponding to one investment into UniV3 interval.

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

    def deposit(self, c: float, y: float) -> float:
        """
        Adds ``y`` tokens to position. Tokens are assumed to be converted to token ``X``
        so that ``x`` / ``y`` ratio is optimal with no slippage and invested into uniV3 pool

        :param c: Current price
        :param y: Amount of ``Y`` token
        :return: Liquidity added
        """

        delta_l = y / y_per_l(self.a, self.b, c)
        self.l += delta_l
        self._bi_x += y / c / 2
        self._bi_y += y / 2
        return delta_l

    def withdraw(self, c: float, l: float) -> float:
        """
        Withdraws ``l`` liquidity from the position. UniV3 returns ``X`` and ``Y`` tokens and all ``X`` tokens
        are converted to ``Y`` tokens at current price with no slippage.

        :param c: Current price
        :param l: Amount of liquidity to withdraw
        :return: amount of ``Y`` token after withdrawal
        """
        self.l -= l
        delta_y = l * y_per_l(self.a, self.b, c)
        self._bi_x -= delta_y / c / 2
        self._bi_y -= delta_y / 2
        return delta_y

    def y(self, c: float) -> float:
        """
        The value of the current position denominated in ``Y`` token. Doesn't include fees collected.

        :param c: Current price
        :return: amount of ``Y`` token if the position is fully withdrawn
        """

        return self.l * y_per_l(self.a, self.b, c)

    def l(self) -> float:
        """
        Current liquidity
        """
        return self._l

    def a(self) -> float:
        """
        Left bound of the price interval
        """
        return self._a

    def a(self, new_a: float, c: float):
        """
        Sets the new left interval bound. The position is fully withdrawn and then deposited in the new interval.

        :param new_a: New Left price bound value
        :param c: Current price
        """
        y = self.withdraw(c, self.l)
        self._a = new_a
        self.deposit(c, y)

    def b(self) -> float:
        """
        Right bound of the price interval
        """

        return self._b

    def b(self, new_b: float, c: float):
        """
        Sets the new right interval bound. The position is fully withdrawn and then deposited in the new interval.

        :param new_a: New right price bound value
        :param c: Current price
        """

        y = self.withdraw(c, self.l)
        self._b = new_b
        self.deposit(c, y)

    def active_l(self, c: float) -> float:
        """
        The amount of currently active liquidity

        :param c: Current price
        :return: The amount of liquidity or 0 if price is out of (a, b) bounds
        """
        if c <= self.b and c >= self.a:
            return self.l
        return 0

    def il(self, c: float) -> float:
        """
        The amount of current impermanent loss

        :param c: Current price
        :return: The amount of current impermanent loss
        """
        bicurrency_payoff = self._bi_x * c + self._bi_y
        return bicurrency_payoff - self.y(c)

    def __str__(self):
        return f"(a: {self.a}, b: {self.b}, l: {self.l})"
