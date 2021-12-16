import numpy as np
from decimal import Decimal


def price_after_swap_y_to_x(dy, l, p_0):
    """Calculate price after swap y tokens to x, having l liquidity.
        All entities are defined in weis/satoshi.

    Args:
        dy (float64): y tokens to be swapped to x
        l (float64): current liquidity
        p_0 (float64): price before swap

    Returns:
        p_1 (float64): price after swap
    """
    dy_l = Decimal(dy) / Decimal(l)
    sqrt_p_1 = dy_l + np.sqrt(Decimal(p_0))
    p_1 = np.power(sqrt_p_1, 2)
    return float(p_1)


def price_after_swap_x_to_y(dx, l, p_0):
    """Calculate price after swap x tokens to y, having l liquidity.
        All entities are defined in weis/satoshi.

    Args:
        dx (float64): x tokens to be swapped to y
        l (float64): current liquidity
        p_0 (float64): price before swap

    Returns:
        p_1 (float64): price after swap
    """
    dx_l = Decimal(dx) / Decimal(l)
    denom = dx_l + np.sqrt(1 / Decimal(p_0))
    sqrt_p_1 = 1 / denom
    p_1 = np.power(sqrt_p_1, 2)
    return float(p_1)


def tokens_x_after_swap_y_to_x(dy, l):
    dy_l = Decimal(dy) / Decimal(l)
    dx = Decimal(l) / dy_l
    return dx