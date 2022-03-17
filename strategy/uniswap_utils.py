import numpy as np


class UniswapLiquidityAligner:
    """
    UniswapLiquidityAligner this is a class with standard uniswap V3 formulas and transformations
    related to liquidity on the interval.

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
            real_price = y/x
        """

        sqrt_price = np.sqrt(price)
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)

        if sqrt_upper <= sqrt_price:
            return np.inf

        elif sqrt_lower >= sqrt_price:
            return 0.

        return (sqrt_price - sqrt_lower) * sqrt_upper * sqrt_price / (sqrt_upper - sqrt_price)

    def x_to_liq(self, price, x):
        """
        Args:
            price: current market price
            x: amount of X tokens

        Returns:
            The amount of liquidity for the given price and amount of tokens X
        """

        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_price >= sqrt_upper:
            return 0.

        left_bound = max(sqrt_lower, sqrt_price)

        return x * (sqrt_upper * left_bound) / (sqrt_upper - left_bound)

    def y_to_liq(self, price, y):
        """
        Args:
            price: current market price
            y: amount of Y tokens

        Returns:
            The amount of liquidity for the given price and amount of tokens Y
        """

        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_price <= sqrt_lower:
            return 0.

        right_bound = min(sqrt_price, sqrt_upper)

        return y / (right_bound - sqrt_lower)

    def xy_to_liq(self, price, x, y):
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

        liq_x = self.x_to_liq(price=price, x=x)
        liq_y = self.y_to_liq(price=price, y=y)

        if price >= self.upper_price:
            return liq_y

        if price <= self.lower_price:
            return liq_x

        return min(liq_x, liq_y)

    def liq_to_x(self, price, liq):
        """
        Args:
            price: current market price
            liq: given amount of liquidity

        Returns:
            The amount of token X for a given amount of liquidity and a price range
        """
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_price >= sqrt_upper:
            return 0.

        left_bound = max(sqrt_lower, sqrt_price)

        return liq * (sqrt_upper - left_bound) / (left_bound * sqrt_upper)

    def liq_to_y(self, price, liq):
        """
        Args:
            price: current market price
            liq: given amount of liquidity

        Returns:
            The amount of token Y for a given amount of liquidity and market price
        """
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)
        sqrt_price = np.sqrt(price)

        if sqrt_price <= sqrt_lower:
            return 0.
        right_bound = min(sqrt_price, sqrt_upper)
        return liq * (right_bound - sqrt_lower)

    def liq_to_xy(self, price, liq):
        """

        Args:
            price: current market price
            liq: amount of liquidity to be allocated
        Returns:
            The amount of X tokens and the amount of Y tokens that must be allocated to provide required amount of
            liquidity at a given interval and price
        """
        assert liq >= 0, f'Incorrect liquidity {liq}'
        assert price > 1e-16, f'Incorrect price = {price}'
        amount_x = self.liq_to_x(price, liq)
        amount_y = self.liq_to_y(price, liq)
        return amount_x, amount_y

    def check_xy_is_optimal(self, price, x, y):
        """
        Args:
            price: current market price
            x: amount of X tokens
            y: amount of Y tokens

        Returns:
            (is_optimal, x_liq, y_liq):
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

        liq_x = self.x_to_liq(price=price, x=x)
        liq_y = self.y_to_liq(price=price, y=y)

        if sqrt_price <= sqrt_lower:
            return y < 1e-6, liq_x, liq_y

        if sqrt_price >= sqrt_upper:
            return x < 1e-6, liq_x, liq_y

        return abs(liq_x - liq_y) < 1e-6, liq_x, liq_y


# class UniswapV3Utils:
#     """
#     ``UniV3Utils`` is a class for creating UniswapV3 position in correct proportions.
#
#     Attributes:
#         lower_0: Base lower bound of the emulated interval.
#         upper_0: Base upper bound of the emulated interval.
#     """
#     def __init__(self,
#                  lower_0: float,
#                  upper_0: float,
#                  ):
#         self.lower_0 = lower_0
#         self.upper_0 = upper_0
#
#     def calc_fraction_to_uni(self, price, lower_price, upper_price):
#         """
#         TODO:
#         Args:
#             price:
#             lower_price:
#             upper_price:
#
#         Returns:
#
#         """
#         numer = 2 * np.sqrt(price) - np.sqrt(lower_price) - price / np.sqrt(upper_price)
#         denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
#         res = numer / denom
#         if res > 1:
#             print(f'Warning fraction Uni = {res}')
#         elif res < 0:
#             print(f'Warning fraction Uni = {res}')
#         return res
#
#     def calc_fraction_to_x(self, price, upper_price):
#         """
#         TODO:
#         Args:
#             price:
#             upper_price:
#
#         Returns:
#
#         """
#         numer = price / np.sqrt(upper_price) - price / np.sqrt(self.upper_0)
#         denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
#         res = numer / denom
#         if res > 1:
#             print(f'Warning fraction X = {res}')
#         elif res < 0:
#             print(f'Warning fraction X = {res}')
#         return res
#
#     def calc_fraction_to_y(self, price, lower_price):
#         """
#         TODO:
#         Args:
#             price:
#             lower_price:
#
#         Returns:
#
#         """
#         numer = np.sqrt(lower_price) - np.sqrt(self.lower_0)
#         denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
#         res = numer / denom
#         if res > 1:
#             print(f'Warning fraction Y = {res}')
#         elif res < 0:
#             print(f'Warning fraction Y = {res}')
#         return res
#
#
# class UniswapV2Utils:
#     """
#     TODO:
#     """
#     def calc_fraction_to_uni(self, price, lower_price, upper_price):
#         """
#         TODO:
#         Args:
#             price:
#             lower_price:
#             upper_price:
#
#         Returns:
#
#         """
#         res = 1 - self.calc_fraction_to_y(price, lower_price) - self.calc_fraction_to_x(price, upper_price)
#         if res > 1:
#             print(f'Warning fraction Uni = {res}')
#         elif res < 0:
#             print(f'Warning fraction Uni = {res}')
#         return res
#
#     def calc_fraction_to_x(self, price, upper_price):
#         """
#         TODO:
#         Args:
#             price:
#             upper_price:
#
#         Returns:
#
#         """
#         numer = np.sqrt(price)
#         denom = 2 * np.sqrt(upper_price)
#         res = numer / denom
#         if res > 1:
#             print(f'Warning fraction X = {res}')
#         elif res < 0:
#             print(f'Warning fraction X = {res}')
#         return res
#
#     def calc_fraction_to_y(self, price, lower_price):
#         """
#         TODO:
#         Args:
#             price:
#             lower_price:
#
#         Returns:
#
#         """
#         numer = np.sqrt(lower_price)
#         denom = 2 * np.sqrt(price)
#         res = numer / denom
#         if res > 1:
#             print(f'Warning fraction Y = {res}')
#         elif res < 0:
#             print(f'Warning fraction Y = {res}')
#         return res
