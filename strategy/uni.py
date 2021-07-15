"""
``uni`` module contains helper functions for math in Uniswap V3 pools.
"""

from typing import Tuple
import numpy as np


def y_per_l(a: float, b: float, c: float) -> float:
    """
    Amount of ``Y`` token equivalent to a unit of liquidity.

    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :returns: Amount of ``Y`` token you will receive if you remove one liquidity unit, get ``x`` and ``y`` tokens
              and sell ``x`` at price `c` with no slippage
    """
    mc = min(max(a, c), b)
    return c * (1 / np.sqrt(mc) - 1 / np.sqrt(b)) + np.sqrt(mc) - np.sqrt(a)


def l_per_y(a: float, b: float, c: float) -> float:
    """
    Amount of liquidity equivalent to a unit of token ``Y``.

    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :return: Amount of liquidity you will receive if you invest one unit of ``Y``, convert optimal portion to token ``X``
             with no slippage and invest into uniV3 pool
    """

    return 1 / y_per_l(a, b, c)


def c_real(a: float, b: float, c: float) -> float:
    sa, sb, sc = np.sqrt(a), np.sqrt(b), np.sqrt(c)
    if sb == sc:
        return np.inf
    return (sc - sa) * sb * sc / (sb - sc)


def align_for_liquidity(
    x: float, y: float, a: float, b: float, c: float, fee_percent: float
) -> Tuple[float, float]:
    cr = c_real(a, b, c)
    z = cr * x - y
    d = 1 - fee_percent if z >= 0 else 1 / (1 - fee_percent)
    dx = z / (c * d + cr)
    return x - dx, y + c * d * dx


def liq0(x: float, b: float, c: float) -> float:
    if b <= c:
        return np.inf
    sb, sc = np.sqrt(b), np.sqrt(c)
    if sb == sc:
        return np.inf
    return x * sb * sc / (sb - sc)


def liq1(y: float, a: float, c: float) -> float:
    if a >= c:
        return np.inf
    sa, sc = np.sqrt(a), np.sqrt(c)
    if sa == sc:
        return np.inf
    return y / (sc - sa)


def liq(x: float, y: float, a: float, b: float, c: float) -> float:
    return min(liq0(x, b, c), liq1(y, a, c))


def xy(l: float, a: float, b: float, c: float) -> Tuple[float, float]:
    x = 1 / liq0(l, b, c)
    y = 1 / liq1(l, a, c)
    return x, y
