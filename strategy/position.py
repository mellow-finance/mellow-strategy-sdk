class Position:
    """
    Position is a primitive corresponding to one investment into UniV3 interval
    """

    def __init__(self, id, a, b):
        self._id = id
        self._a = a
        self._b = b
        self._l = 0
        self._bi_y = 0
        self._bi_x = 0

    """
    @notice adds y token to position
    @param price - current price
    @param y - amount of y token
    @return liquidity added
    """

    def deposit(self, price, y):
        delta_l = y / y_per_l(self.a, self.b, price)
        self.l += delta_l
        self._bi_x += y / price / 2
        self._bi_y += y / 2
        return delta_l

    """
    @notice adds liquidity to posision
    @param price - current price
    @param l - current liquidity
    @return value lost
    """

    def withdraw(self, price, l):
        self.l -= l
        delta_y = l * y_per_l(self.a, self.b, price)
        self._bi_x -= delta_y / price / 2
        self._bi_y -= delta_y / 2
        return delta_y

    """
    @notice current value of the position
    @param price - current price
    """

    def y(self, price):
        return self.l * y_per_l(self.a, self.b, price)

    """
    @notice returns liquidity of the position
    """

    def l(self):
        return self._l

    """
    @notice returns left interval of the position
    """

    def a(self):
        return self._a

    """
    @notice sets new `a` bound and reinvests accordingly
    @param _a new `a` param
    @param price current price
    """

    def a(self, _a, price):
        y = self.withdraw(price, self.l)
        self._a = _a
        self.deposit(price, y)

    """
    @notice returns right interval of the position
    """

    def b(self):
        return self._b

    """
    @notice sets new `b` bound and reinvests accordingly
    @param _b new `b` param
    @param price current price
    """

    def b(self, _b, price):
        y = self.withdraw(price, self.l)
        self._b = _b
        self.deposit(price, y)

    """
    @notice gives the amount of liquidity or 0 if price is out of bounds
    """

    def active_l(self, price):
        if price <= self.b and price >= self.a:
            return self.l
        return 0

    """
    @notice current impermanent loss of the position
    @param price - current price
    """

    def il(self, price):
        bicurrency_payoff = self._bi_x * price + self._bi_y
        return bicurrency_payoff - self.y(price)

    def __str__(self):
        return f"(a: {self.a}, b: {self.b}, l: {self.l})"
