from .Portfolio import Portfolio
from .Positions import UniV3Position

import numpy as np


class PortfolioFabric:
    def __init__(self, position):
        self.position = position

    def create(self, *args, **kwargs):
        position = self.position(**kwargs)
        portfolio = Portfolio('main', [position])
        return portfolio


# class StrategyFabric:
#     def __init__(self, strategy, portfolio):
#         self.strategy = strategy
#         self.portfolio = portfolio
#
#     def create(self, *args, **kwargs):
#         position = self.position(**kwargs)
#         portfolio = Portfolio('main', [position])
#         return portfolio


class UniV3Fabric:
    def __init__(self,
                 portfolio: Portfolio,
                 lower_0: float,
                 upper_0: float,
                 fee_percent: float,
                 rebalance_cost: float,
                 ):
        self.portfolio = portfolio
        self.lower_0 = lower_0
        self.upper_0 = upper_0
        self.fee_percent = fee_percent
        self.rebalance_cost = rebalance_cost

    def create_uni_position(self, name, lower_price, upper_price, price):
        vault = self.portfolio.get_position('Vault')
        x_all, y_all = vault.to_xy(price)

        fraction_uni = self._calc_fraction_to_uni_(lower_price, upper_price, price)
        x_uni, y_uni = x_all * fraction_uni, y_all * fraction_uni
        x_uni_aligned, y_uni_aligned = self._align_to_liq_(x_uni, y_uni, lower_price, upper_price, price)
        vault.withdraw(x_uni_aligned, y_uni_aligned)

        univ3_pos = UniV3Position(name, lower_price, upper_price, self.fee_percent, self.rebalance_cost)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)

        fraction_x = self._calc_fraction_to_x_(upper_price, price) / (1 - fraction_uni)
        fraction_y = self._calc_fraction_to_y_(lower_price, price) / (1 - fraction_uni)
        vault.rebalance(fraction_x, fraction_y, price)
        return univ3_pos

    def _calc_fraction_to_uni_(self, lower_price, upper_price, price):
        numer = 2 * np.sqrt(price) - np.sqrt(lower_price) - price / np.sqrt(upper_price)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Uni = {res}')
        elif res < 0:
            print(f'Warning fraction Uni = {res}')
        return res

    def _calc_fraction_to_x_(self, upper_price, price):
        numer = price / np.sqrt(upper_price) - price / np.sqrt(self.upper_0)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction X = {res}')
        elif res < 0:
            print(f'Warning fraction X = {res}')
        return res

    def _calc_fraction_to_y_(self, lower_price, price):
        numer = np.sqrt(lower_price) - np.sqrt(self.lower_0)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Y = {res}')
        elif res < 0:
            print(f'Warning fraction Y = {res}')
        return res

    def _real_price_(self, lower_price: float, upper_price: float, price: float) -> float:
        sqrt_lower = np.sqrt(lower_price)
        sqrt_upper = np.sqrt(upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_upper <= sqrt_price:
            return np.inf
        elif sqrt_lower >= sqrt_price:
            return 0

        numer = (sqrt_price - sqrt_lower) * sqrt_upper * sqrt_price
        denom = sqrt_upper - sqrt_price
        coef = numer / denom
        return coef

    def _align_to_liq_(self, x: float, y: float, lower_price: float, upper_price: float, price: float):
        v_y = price * x + y
        price_real = self._real_price_(lower_price, upper_price, price)
        if price_real == np.inf:
            x_new = 0
            y_new = v_y
        else:
            x_new = v_y / (price + price_real)
            y_new = price_real * x_new
        return x_new, y_new
