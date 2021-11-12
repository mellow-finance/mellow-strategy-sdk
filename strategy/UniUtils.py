import numpy as np


class UniswapV3Utils:
    """
       ``UniV3Utils`` is a class for creating UniswapV3 position in correct proportions.
       :param lower_0: Base lower bound of the emulated interval
       :param upper_0: Base upper bound of the emulated interval
    """
    def __init__(self,
                 lower_0: float,
                 upper_0: float,
                 ):
        self.lower_0 = lower_0
        self.upper_0 = upper_0

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
