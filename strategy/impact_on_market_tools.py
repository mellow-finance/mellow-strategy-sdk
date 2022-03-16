from decimal import Decimal
import numpy as np


def price_after_swap_y_to_x(dy: float, liq: float, p_0: float) -> float:
    """
    Price after swap Y token to X.
    Args:
        dy: Amount of token Y to swap.
        liq: Liquidity on current tick.
        p_0: Price before swap.
    Returns:
        Price after swap.
    """
    dsqrt_p = Decimal(dy) / Decimal(liq)
    sqrt_p_1 = dsqrt_p + np.sqrt(Decimal(p_0))
    p_1 = np.power(sqrt_p_1, 2)
    return float(p_1)


def price_after_swap_x_to_y(dx: float, liq: float, p_0: float) -> float:
    """
    Price after swap X token to Y.
    Args:
        dx: Amount of token X to swap.
        liq: Liquidity on current tick.
        p_0: Price before swap.
    Returns:
        Price after swap.
    """
    dsqrt_p = Decimal(dx) / Decimal(liq)
    denom = dsqrt_p + np.sqrt(1 / Decimal(p_0))
    sqrt_p_1 = 1 / denom
    p_1 = np.power(sqrt_p_1, 2)
    return float(p_1)


def tokens_x_after_swap_y_to_x(dy: float, liq: float, p_0: float) -> float:
    """
    Tokens X after swap Y token to X.
    Args:
        dy: Amount of token Y to swap.
        liq: Liquidity on current tick.
        p_0: Price before swap.
    Returns:
        Amount of token X after swap.
    """
    dsqrt_p = Decimal(dy) / Decimal(liq)
    sqrt_p_1 = dsqrt_p + np.sqrt(Decimal(p_0))
    numer = - Decimal(liq) * dsqrt_p
    denom = np.sqrt(Decimal(p_0)) * sqrt_p_1
    dx = numer / denom
    return float(dx)


def tokens_y_after_swap_x_to_y(dx: float, liq: float, p_0: float) -> float:
    """
    Tokens Y after swap X token to Y.
    Args:
        dx: Amount of token Y to swap.
        liq: Liquidity on current tick.
        p_0: Price before swap.
    Returns:
        Amount of token Y after swap.
    """
    dsqrt_p = Decimal(dx) / Decimal(liq)
    denom = dsqrt_p + np.sqrt(1 / Decimal(p_0))
    sqrt_p_1 = 1 / denom
    dy = - Decimal(liq) * dsqrt_p * sqrt_p_1 * np.sqrt(Decimal(p_0))
    return float(dy)


def tokens_y_for_swap_p_0_to_p_1(liq: float, p_0: float, p_1: float) -> float:
    """
    Tokens Y for move price from p_0 to p_1.
    Args:
        liq: Liquidity on current tick.
        p_0: Price before swap.
        p_1: Price after swap.
    Returns:
        Amount of token Y.
    """
    dsqrt_p = np.sqrt(Decimal(p_1)) - np.sqrt(Decimal(p_0))
    dy = dsqrt_p * liq
    return dy


def tokens_x_for_swap_p_0_to_p_1(liq: float, p_0: float, p_1: float) -> float:
    """
    Tokens X for move price from p_0 to p_1.
    Args:
        liq: Liquidity on current tick.
        p_0: Price before swap.
        p_1: Price after swap.
    Returns:
        Amount of token X.
    """
    dsqrt_p = np.sqrt(Decimal(1 / p_1)) - np.sqrt(Decimal(1 / p_0))
    dx = dsqrt_p * liq
    return dx
