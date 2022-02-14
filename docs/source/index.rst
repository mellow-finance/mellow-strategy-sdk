Mellow Strategy SDK
===============================================

Mellow Stratedy SDK is a set of tools for defining custom strategies 
and backtesting them on real `Uniswap V3 <https://uniswap.org/whitepaper-v3.pdf>`_ data in just a few steps.

Currently the data is available for the following pools:

- WBTC / WETH
- USDC / WETH
- USDC / USDT

The SDK is assumed to be used in Jupyter notebooks and optimized for displaying 
and working data in a form of `Pandas <https://pandas.pydata.org/>`_ Dataframes and Series.

To start using the SDK see :ref:`Getting Started`.

Notation
~~~~~~~~

Each pool is assumed to contain ``X`` and ``Y`` tokens and lower ``x`` and ``y`` are the amounts of the tokens respectively.

- ``a`` - the lower price for Uniswap V3 position (:math:`p_a` from the whitepaper)
- ``b`` - the upper price for Uniswap V3 position (:math:`p_b` from the whitepaper)
- ``l`` - the amount of virtual liquidity for the position (:math:`l` from the whitepaper)
- ``c`` - the current price. ``c`` = ``y`` / ``x``

.. toctree::
   :maxdepth: 3
   :caption: User guide

   getting_started


.. toctree::
   :maxdepth: 3
   :caption: API

   strategy

