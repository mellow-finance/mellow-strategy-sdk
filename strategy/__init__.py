"""
``strategy`` package allows to define UniV3 investment strategy, 
i.e. how to change position over time and get the results of backtesting this strategy on different pools.
The basic definitions are used from `Uniswap V3 Whitepaper <https://uniswap.org/whitepaper-v3.pdf>`_

- ``a`` is :math:`p_a` from the whitepaper
- ``b`` is :math:`p_b` from the whitepaper
- ``l`` is the amount of virtual liquidity
- ``c`` is the current price. ``c`` = ``y`` / ``x``

The pool is assumed to contain ``X`` and ``Y`` tokens and lower ``x`` and ``y`` are the amounts of the tokens respectively.

portfolio
---------

.. automodule:: strategy.portfolio

history
-------
.. automodule:: strategy.history

uni
---

.. automodule:: strategy.uni
    :members:
"""
