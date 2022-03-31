SDK for creating new strategies on Uniswap V3

.. code-block:: bash

    git clone https://github.com/mellow-finance/mellow-strategy-sdk.git
    cd mellow-strategy-sdk
    python3 -m venv .venv
    source .venv/bin/activate
    pip install poetry
    poetry install

or

.. code-block:: bash

    pip install mellow_strategy_sdk


Getting Started
==============================


Import
~~~~~~~~~~~~

.. code-block:: python

    from mellow_sdk.primitives import Pool, Token, Fee
    from mellow_sdk.data import RawDataUniV3
    from mellow_sdk.strategies import UniV3Passive
    from mellow_sdk.backtest import Backtest
    from mellow_sdk.viewers import RebalanceViewer, UniswapViewer, PortfolioViewer
    from mellow_sdk.positions import BiCurrencyPosition, UniV3Position

Choose a pool
~~~~~~~~~~~~~~~~

A typical notebook would start with downloading and preparing data for a specific pool.
``POOLS`` is a list of available pools, let's choose 1 it is WBTC/WETH, fee 0.3%

.. code-block:: python

    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)

Get data
~~~~~~~~~~~~

Аt the first run you need to download the data

.. code-block:: python

    data = RawDataUniV3(pool, 'data', reload_data=False).load_from_folder()


Use implemented strategy
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    univ3_passive = UniV3Passive(
        lower_price=data.swaps['price'].min() - 1,
        upper_price=data.swaps['price'].max() + 1,
        pool=pool,
        gas_cost=0.,
        name='passive'
    )


Backtest
~~~~~~~~~~~~

Next step is to run backtest using your strategy and data

.. code-block:: python

    bt = Backtest(univ3_passive)
    portfolio_history, rebalance_history, uni_history = bt.backtest(data.swaps)

Visualize
~~~~~~~~~~~~

Next visualize results

.. code-block:: python

    rv = RebalanceViewer(rebalance_history)
    uv = UniswapViewer(uni_history)
    pv = PortfolioViewer(portfolio_history, pool)

    # Draw portfolio stats, like value, fees earned, apy
    fig1, fig2, fig3, fig4, fig5, fig6 = pv.draw_portfolio()

    # Draw Uniswap intervals
    intervals_plot = uv.draw_intervals(data.swaps)

    # Draw rebalances
    rebalances_plot = rv.draw_rebalances(data.swaps)

    # Calculate df with portfolio stats
    stats = portfolio_history.calculate_stats()

If you have a powerful pc and a good connection you can remove render='svg'

.. code-block:: python

    intervals_plot.show(render='svg')

.. image:: https://raw.githubusercontent.com/mellow-finance/mellow-strategy-sdk/main/examples/getting_started_intervals.png


.. code-block:: python

    rebalances_plot.show(render='svg')

.. image:: https://raw.githubusercontent.com/mellow-finance/mellow-strategy-sdk/main/examples/getting_started_rebalances.png

.. code-block:: python

    fig2.show(render='svg')

.. image:: https://raw.githubusercontent.com/mellow-finance/mellow-strategy-sdk/main/examples/getting_started_fig2.png

.. code-block:: python

    fig4.show(render='svg')

.. image:: https://raw.githubusercontent.com/mellow-finance/mellow-strategy-sdk/main/examples/getting_started_fig4.png

.. code-block:: python

    fig6.show(render='svg')

.. image:: https://raw.githubusercontent.com/mellow-finance/mellow-strategy-sdk/main/examples/getting_started_fig6.png

Congratulations! Now you have the results of your strategy backtest on the real UniV3 data!
