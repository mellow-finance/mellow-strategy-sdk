"""
``uni`` module contains helper functions for math in Uniswap V3 pools.
"""

from decimal import Decimal


def y_per_l(a, b, c):
    """
    Amount of ``Y`` token equivalent to a unit of liquidity.

    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :returns: Amount of ``Y`` token you will receive if you remove one liquidity unit, get ``x`` and ``y`` tokens
              and sell ``x`` at price `c` with no slippage
    """
    mc = min(max(a, c), b)
    return (
        c * (1 / Decimal.sqrt(mc) - 1 / Decimal.sqrt(b))
        + Decimal.sqrt(mc)
        - Decimal.sqrt(a)
    )


def l_per_y(a, b, c):
    """
    Amount of liquidity equivalent to a unit of token ``Y``.

    :param a: Left bound of liquidity interval (price)
    :param b: Right bound of liquidity interval (price)
    :param c: Current price
    :return: Amount of liquidity you will receive if you invest one unit of ``Y``, convert optimal portion to token ``X``
    with no slippage and invest into uniV3 pool
    """

    return 1 / y_per_l(a, b, c)
