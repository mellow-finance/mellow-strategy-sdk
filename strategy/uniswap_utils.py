"""
TODO write
"""
import numpy as np


class UniswapLiquidityAligner:
    """
    ``UniswapLiquidityAligner`` is a class with UniswapV3 utils.

    Attributes:
        lower_price: Left bound for the UniswapV3 interval.
        upper_price: Right bound for the UniswapV3 interval.
        TODO: что он делает?
    """
    def __init__(self, lower_price, upper_price):
        self.lower_price = lower_price
        self.upper_price = upper_price

    def real_price(self, price: float) -> float:
        """
        Args:
            price: current price on market

        Returns:
            TODO: this
        """
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_upper <= sqrt_price:
            return np.inf
        elif sqrt_lower >= sqrt_price:
            return 0
        # TODO: откуда формулы?
        numer = (sqrt_price - sqrt_lower) * sqrt_upper * sqrt_price
        denom = sqrt_upper - sqrt_price
        coef = numer / denom
        return coef

    def align_to_liq(self, x: float, y: float, price: float):
        """
        Args:
            TODO: this
            x:
            y:
            price: current price on market

        Returns:

        """
        # TODO: вставить комиссию за обмены
        v_y = price * x + y
        price_real = self.real_price(price)
        if np.isinf(price_real):
            x_new = 0
            y_new = v_y
            # TODO: чет я не понимаю, у нас становится inf y_new?
        else:
            # TODO: чет тоже хз что здесь происходит
            x_new = v_y / (price + price_real)
            y_new = price_real * x_new
        return x_new, y_new


class UniswapV3Utils:
    """
    ``UniV3Utils`` is a class for creating UniswapV3 position in correct proportions.

    Attributes:
        lower_0: Base lower bound of the emulated interval.
        upper_0: Base upper bound of the emulated interval.
    """
    def __init__(self,
                 lower_0: float,
                 upper_0: float,
                 ):
        self.lower_0 = lower_0
        self.upper_0 = upper_0

    def calc_fraction_to_uni(self, price, lower_price, upper_price):
        """
        TODO:
        Args:
            price:
            lower_price:
            upper_price:

        Returns:

        """
        numer = 2 * np.sqrt(price) - np.sqrt(lower_price) - price / np.sqrt(upper_price)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Uni = {res}')
        elif res < 0:
            print(f'Warning fraction Uni = {res}')
        return res

    def calc_fraction_to_x(self, price, upper_price):
        """
        TODO:
        Args:
            price:
            upper_price:

        Returns:

        """
        numer = price / np.sqrt(upper_price) - price / np.sqrt(self.upper_0)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction X = {res}')
        elif res < 0:
            print(f'Warning fraction X = {res}')
        return res

    def calc_fraction_to_y(self, price, lower_price):
        """
        TODO:
        Args:
            price:
            lower_price:

        Returns:

        """
        numer = np.sqrt(lower_price) - np.sqrt(self.lower_0)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Y = {res}')
        elif res < 0:
            print(f'Warning fraction Y = {res}')
        return res


class UniswapV2Utils:
    """
    TODO:
    """
    def calc_fraction_to_uni(self, price, lower_price, upper_price):
        """
        TODO:
        Args:
            price:
            lower_price:
            upper_price:

        Returns:

        """
        res = 1 - self.calc_fraction_to_y(price, lower_price) - self.calc_fraction_to_x(price, upper_price)
        if res > 1:
            print(f'Warning fraction Uni = {res}')
        elif res < 0:
            print(f'Warning fraction Uni = {res}')
        return res

    # TODO static
    def calc_fraction_to_x(self, price, upper_price):
        """
        TODO:
        Args:
            price:
            upper_price:

        Returns:

        """
        numer = np.sqrt(price)
        denom = 2 * np.sqrt(upper_price)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction X = {res}')
        elif res < 0:
            print(f'Warning fraction X = {res}')
        return res

    # TODO static
    def calc_fraction_to_y(self, price, lower_price):
        """
        TODO:
        Args:
            price:
            lower_price:

        Returns:

        """
        numer = np.sqrt(lower_price)
        denom = 2 * np.sqrt(price)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Y = {res}')
        elif res < 0:
            print(f'Warning fraction Y = {res}')
        return res
