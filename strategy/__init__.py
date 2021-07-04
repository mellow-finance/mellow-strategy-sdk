"""
``strategy`` is a top-level package of Mellow Stratedy SDK. 
The key purpose of the package is to enable defining custom strategies and backtesting them on real Uniswap V3 data.

The basic definitions in the package are used from `Uniswap V3 Whitepaper <https://uniswap.org/whitepaper-v3.pdf>`_

The pool is assumed to contain ``X`` and ``Y`` tokens and lower ``x`` and ``y`` are the amounts of the tokens respectively.

- ``a`` - the lower price for Uniswap V3 position (:math:`p_a` from the whitepaper)
- ``b`` - the upper price for Uniswap V3 position (:math:`p_b` from the whitepaper)
- ``l`` - the amount of virtual liquidity for the position (:math:`l` from the whitepaper)
- ``c`` - the current price. ``c`` = ``y`` / ``x``

The main packages are:

- ``data`` - getting price and volume UniV3 pool data, transforming, etc.
- ``portfolio`` - models uniswaps position and portfolios (a set of positions)
- ``primitives`` - basic types like enums, etc.
- ``backtest`` - used for defining strategies and backtesting them on UniV3 data

Currently data is available for 3 pools:

- WBTC / WETH
- USDC / WETH
- USDC / USDT
"""

__version__ = "0.1.0"
