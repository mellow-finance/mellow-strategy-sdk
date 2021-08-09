"""
``uni`` module contains helper functions for math in Uniswap V3 pools.
"""

from typing import Tuple
import numpy as np


def c_real(a: float, b: float, c: float) -> float:
    """
    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :return: Optimal token ratio such that Lx = Ly
    """
    sa, sb, sc = np.sqrt(a), np.sqrt(b), np.sqrt(c)
    if sb <= sc:
        return np.inf
    if sa >= sc:
        return 0
    return (sc - sa) * sb * sc / (sb - sc)


def align_for_liquidity(
    x: float, y: float, a: float, b: float, c: float, fee_percent: float
) -> Tuple[float, float]:
    """
    :param x: Amount of ``X`` token
    :param y: Amount of ``Y`` token
    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :param fee_percent:  Fee for the current pool, e.g. 0.003
    :return: Tuple of ``X`` and ``Y`` tokens
    """
    cr = c_real(a, b, c)
    if cr == np.inf:
        return 0, y + c * x * (1 - fee_percent)
    z = cr * x - y
    d = 1 - fee_percent if z >= 0 else 1 / (1 - fee_percent)
    dx = z / (c * d + cr)
    return x - dx, y + c * d * dx


def liq0(x: float, b: float, c: float) -> float:
    """
    :param x: Amount of token ``X``
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :return: Liquidity of ``X`` token
    """
    if b <= c:
        return np.inf
    sb, sc = np.sqrt(b), np.sqrt(c)
    return x * sb * sc / (sb - sc)


def liq1(y: float, a: float, c: float) -> float:
    """
    :param y: Amount of token ``Y``
    :param a: Left bound of liquidity interval (price)
    :param c: Current price
    :return: Liquidity of ``Y`` token
    """
    if a >= c:
        return np.inf
    sa, sc = np.sqrt(a), np.sqrt(c)
    return y / (sc - sa)


def liq(x: float, y: float, a: float, b: float, c: float) -> float:
    """
    :param x: Amount of token ``X``
    :param y: Amount of token ``Y``
    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :return: Liquidity
    """
    cc = min(max(a, c), b)
    return min(liq0(x, b, cc), liq1(y, a, cc))


def xy(l: float, a: float, b: float, c: float) -> Tuple[float, float]:
    """
    :param l: Liquidity
    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :return: Amount of ``X`` and ``Y`` tokens if the position is fully withdrawn
    """
    cc = min(max(a, c), b)
    x = l / liq0(1, b, cc)
    y = l / liq1(1, a, cc)
    return x, y
