"""
TODO write
    UniswapLiquidityAligner and other utils classes
"""

import numpy as np


class UniswapLiquidityAligner:
    """
    UniswapLiquidityAligner this is a class with standard uniswap V3 formulas and transformations
    related to liquidity on the interval

    Attributes:
        lower_price: Left bound for the UniswapV3 interval.
        upper_price: Right bound for the UniswapV3 interval.
    """
    def __init__(self, lower_price, upper_price):
        assert lower_price > 0, f'incorect lower_price {lower_price}'
        assert upper_price > 0, f'incorect upper_price {upper_price}'
        self.lower_price = lower_price
        self.upper_price = upper_price

    def real_price(self, price: float) -> float:
        """
        Args:
            price: current price on market
        Returns:
            TODO: this
        """

        sqrt_price = np.sqrt(price)
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)

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
            # TODO: здесь происходит swap по странной формуле
            x_new = v_y / (price + price_real)
            y_new = price_real * x_new
        return x_new, y_new

    @staticmethod
    def _x_to_liq(sqrt_lower, sqrt_upper, x):
        """
            Correct only when price <= price_lower
        Args:
            sqrt_lower: sqrt of lower_price of interval
            sqrt_upper: sqrt of upper_price of interval
            x: amount of X tokens

        Returns:
            The amount of liquidity for the given price range and amount of tokens X
            at situation price <= price_lower
        """
        return x * (sqrt_upper * sqrt_lower) / (sqrt_upper - sqrt_lower)

    @staticmethod
    def _y_to_liq(sqrt_lower, sqrt_upper, y):
        """
            Correct only when price >=  price_upper
        Args:
            sqrt_lower: sqrt of lower_price of interval
            sqrt_upper: sqrt of upper_price of interval
            y: amount of Y tokens

        Returns:
            The amount of liquidity for the given price range and amount of tokens Y
            at situation price >= price_upper
        """

        return y / (sqrt_upper - sqrt_lower)

    def xy_to_optimal_liq(self, price, x, y):
        """
        Args:
            price: current market price
            x: amount of X tokens
            y: amount of Y tokens

        Returns:
            Maximum liquidity that can be obtained for amounts, interval and current price, without swap
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        assert x >= 0,  f'Incorrect x = {x}'
        assert y >= 0, f'Incorrect y = {y}'

        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_price <= sqrt_lower:
            return self._x_to_liq(sqrt_lower, sqrt_upper, x)

        if sqrt_price >= sqrt_upper:
            return self._y_to_liq(sqrt_lower, sqrt_upper, y)

        liq_x = self._x_to_liq(sqrt_price, sqrt_upper, x)
        liq_y = self._y_to_liq(sqrt_lower, sqrt_price, y)

        return min(liq_x, liq_y)

    @staticmethod
    def _liq_to_x(sqrt_lower, sqrt_upper, liq):
        """
           Correct only when price <= price_lower
        Args:
            sqrt_lower: sqrt of lower_price of interval
            sqrt_upper: sqrt of upper_price of interval
            liq: given amount of liquidity

        Returns:
            The amount of token X for a given amount of liquidity and a price range
            at situation price <= price_lower
        """

        return liq * (sqrt_upper - sqrt_lower) / (sqrt_lower * sqrt_upper)

    @staticmethod
    def _liq_to_y(sqrt_lower, sqrt_upper, liq):
        """
            Correct only when price >= price_upper
        Args:
            sqrt_lower: sqrt of lower_price of interval
            sqrt_upper: sqrt of upper_price of interval
            liq: given amount of liquidity

        Returns:
            The amount of token Y for a given amount of liquidity and a price range
            at situation price >= price_upper
        """
        return liq * (sqrt_upper - sqrt_lower)

    def liq_to_optimal_xy(self, price, liq):
        """

        Args:
            price: current market price
            liq: amount of liquidity to be allocated
        Returns:
            The amount of X tokens and the amount of Y tokens that must be allocated to provide liquidity
            at a given interval and price
        """
        assert liq >= 0, f'Incorrect liquidity {liq}'
        assert price > 1e-16, f'Incorrect price = {price}'
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        amount_x = 0
        amount_y = 0
        if sqrt_price <= sqrt_lower:
            amount_x = self._liq_to_x(sqrt_lower, sqrt_upper, liq)
            return amount_x, amount_y
        if sqrt_price < sqrt_upper:
            amount_x = self._liq_to_x(sqrt_price, sqrt_upper, liq)
            amount_y = self._liq_to_y(sqrt_lower, sqrt_price, liq)
            return amount_x, amount_y

        amount_y = self._liq_to_y(sqrt_lower, sqrt_upper, liq)
        return amount_x, amount_y

    def check_xy_is_optimal(self, price, x, y):
        """
        Args:
            price: current market price
            x: amount of X tokens
            y: amount of Y tokens
        Returns:
            (is_optimal, x_liq, y_liq), where:

            is_optimal:
                True: if given amount of X and given amount of Y token can be fully minted
                on given interval at given price
                False: otherwise
            x_liq:
                The amount of liquidity for the given price range and amount of tokens X
            y_liq:
                The amount of liquidity for the given price range and amount of tokens Y
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        assert x >= 0, f'Incorrect x = {x}'
        assert y >= 0, f'Incorrect y = {y}'

        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_price <= sqrt_lower:
            liq_x = self._x_to_liq(sqrt_lower, sqrt_upper, x)
            return y < 1e-6, liq_x, 0.0

        if sqrt_price >= sqrt_upper:
            liq_y = self._x_to_liq(sqrt_lower, sqrt_upper, x)
            return x < 1e-6, 0.0, liq_y

        liq_x = self._x_to_liq(sqrt_price, sqrt_upper, x)
        liq_y = self._y_to_liq(sqrt_lower, sqrt_price, y)

        return abs(liq_x - liq_y) < 1e-6, liq_x, liq_y


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
