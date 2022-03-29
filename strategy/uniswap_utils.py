import numpy as np
from typing import Tuple


class UniswapLiquidityAligner:
    """
    UniswapLiquidityAligner this is a class with standard Uniswap V3 formulas and transformations
    related to liquidity on the interval.

    Attributes:
        lower_price: Left bound for the UniswapV3 interval.
        upper_price: Right bound for the UniswapV3 interval.
    """
    def __init__(self, lower_price, upper_price):
        assert lower_price > 0, f'Incorect lower_price {lower_price}.'
        assert upper_price > 0, f'Incorect upper_price {upper_price}.'
        self.lower_price = lower_price
        self.upper_price = upper_price

    def real_price(self, price: float) -> float:
        """
        Args:
            price: Current price on market.

        Returns:
            real_price = y / x
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
        Calculate the liquidity for a given amount of tokens X, price and a price range.

        Args:
            price: Current market price.
            x: Amount of X tokens.

        Returns:
            The amount of liquidity for the given price and amount of tokens X.
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
        Calculate the liquidity for a given amount of tokens Y, price and a price range.

        Args:
            price: Current market price.
            y: Amount of Y tokens.

        Returns:
            The amount of liquidity for the given price and amount of tokens Y.
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
        Calculate the liquidity for a given amount of tokens X and Y, price and a price range.

        Args:
            price: Current market price.
            x: Amount of X tokens.
            y: Amount of Y tokens.

        Returns:
            Maximum liquidity that can be obtained for amounts, interval and current price, without swap.
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
        Calculate the amount of X tokens for a given amount of liquidity, price and a price range.

        Args:
            price: Current market price.
            liq: Given amount of liquidity

        Returns:
            The amount of token X for a given amount of liquidity and a price range.
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
        Calculate the amount of Y tokens for a given amount of liquidity, price and a price range.

        Args:
            price: Current market price.
            liq: Given amount of liquidity.

        Returns:
            The amount of token Y for a given amount of liquidity and market price.
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
        Calculate the amount of X and Y tokens for a given amount of liquidity, price and a price range.

        Args:
            price: Current market price.
            liq: Amount of liquidity to be allocated.

        Returns:
            The amount of X tokens and the amount of Y tokens that must be allocated to provide required amount of
            liquidity at a given interval and price.
        """
        assert liq >= 0, f'Incorrect liquidity {liq}'
        assert price > 1e-16, f'Incorrect price = {price}'
        amount_x = self.liq_to_x(price, liq)
        amount_y = self.liq_to_y(price, liq)
        return amount_x, amount_y

    def check_xy_is_optimal(self, price, x, y):
        """
        Check if the given amount of X and Y tokens are optimal for a given price and a price range.

        Args:
            price: Current market price.
            x: Amount of X tokens.
            y: Amount of Y tokens.

        Returns:
            (is_optimal, x_liq, y_liq):
                is_optimal:
                    True: if given amount of X and given amount of Y token can be fully minted
                    on given interval at given price.
                    False: otherwise.
                x_liq:
                    The amount of liquidity for the given price range and amount of tokens X.
                y_liq:
                    The amount of liquidity for the given price range and amount of tokens Y.
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

    def get_amounts_for_swap_to_optimal(
            self,
            x: float,
            y: float,
            price: float,
            swap_fee: float
    ) -> Tuple[float, float]:
        """
        Calculate the amount of X or Y tokens that must be swapped to provide optimal liquidity at a given price.

        Args:
            x: Amount of X tokens.
            y: Amount of Y tokens.
            price: Current market price.
            swap_fee: Swap fee.

        Returns:
            (x_swap, y_swap):
                x_swap: Amount of X tokens that must be swapped to provide optimal liquidity at a given price.
                y_swap: Amount of Y tokens that must be swapped to provide optimal liquidity at a given price.
        """
        is_optimal, liq_x, liq_y = self.check_xy_is_optimal(x=x, y=y, price=price)

        if is_optimal:
            return 0., 0.

        if price <= self.lower_price:
            return 0, y

        if price >= self.upper_price:
            return x, 0

        if liq_x > liq_y:
            num = self.x_to_liq(price=price, x=x) - self.y_to_liq(price=price, y=y)
            den = self.x_to_liq(price=price, x=1.) + self.y_to_liq(price=price, y=(1 - swap_fee) * price)
            return num / den, 0

        if liq_x < liq_y:
            num = self.y_to_liq(price=price, y=y) - self.x_to_liq(price=price, x=x)
            den = self.x_to_liq(price=price, x=(1 - swap_fee) / price) + self.y_to_liq(price=price, y=1.)
            return 0, num / den

    def get_amounts_after_optimal_swap(
            self,
            x: float,
            y: float,
            price: float,
            swap_fee: float
    ) -> Tuple[float, float]:
        """
        Calculate the amount of X and Y tokens after optimal swap.
        The amount of X and Y tokens is optimal for a given price and a price range for minting them to UniV3.

        Args:
            x: Amount of X tokens.
            y: Amount of Y tokens.
            price: Current market price.
            swap_fee: Swap fee.

        Returns:
            (x_after_swap, y_after_swap):
                x_after_swap: Amount of X tokens after optimal swap.
                y_after_swap: Amount of Y tokens after optimal swap.
        """
        dx, dy = self.get_amounts_for_swap_to_optimal(x, y, price, swap_fee)

        x -= dx
        y -= dy

        x += dy * (1 - swap_fee) / price
        y += dx * (1 - swap_fee) * price
        return x, y
