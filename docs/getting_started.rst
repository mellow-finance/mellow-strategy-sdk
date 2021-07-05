Getting Started
===============

The easiest way to get started is to clone SDK and use examples in the `Github repo <https://github.com/mellow-finance/mellow-strategy-sdk/tree/main/examples>`_

A typical notebook would start with installing external dependencies::

    import os
    import sys
    root = os.path.split(os.getcwd())[0]
    if root not in sys.path:
        sys.path.append(root)
    !{sys.executable} -m pip install numpy pandas intervaltree matplotlib

    import numpy as np
    import pandas as pd

If you make your own notebook rather than using repo examples then the section
will look like this::

    import sys
    !{sys.executable} -m pip install mellow-stategy-sdk

The next step is to download and prepare the data for a specific pool::

    from strategy import PoolData, Pool, Token, Fee, Frequency
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    data = PoolData.from_pool(pool, Frequency.DAY)
    data.plot() # Optional step to visualize the data in the notebook

Then you define your strategy by inheriting :ref:`class AbstractStrategy` and overriding the ``rebalance`` method::

    from strategy import Position, AbstractStrategy 
    from datetime import datetime
    from typing import Callable

    class TickStrategy(AbstractStrategy):        
        def rebalance(
            self,
            t: datetime,
            c: float,
            vol: float,
            l: Callable[[float], float],
            pool_data: PoolData,
        ) -> bool:
            if not self.portfolio.position("main"):
                self.portfolio.add_position(Position(id="main", a = c / 1.0001 ** 60, b = c * 1.0001 ** 60))
                pos = self.portfolio.position("main")
                pos.deposit(c, 1)
            else:
                pos = self.portfolio.position("main")
                pos.set_a(c / 1.0001 ** 60, c)
                pos.set_b(c * 1.0001 ** 60, c)
                return True

            return False

    strategy = TickStrategy()

Typycally the definition of the ``rebalance`` method would contain two sections:

- `Lazy init`
            On the first call you need to initialize strategy's portfolio under management.
            Here you need to create initial positions with ``add_position``
            method of :ref:`class Portfolio` and invest initial amount using ``deposit`` method.
- `Rebalance`
            In this section you decied if you want to rebalance or not.
            If you rebalance you need to return ``True`` from the rebalance method to account for rebalance costs

The final step is to run backtest using your strategy and data::

    from strategy import Backtest

    backtest = Backtest(strategy)
    backtest.run(data, 0.001)
    backtest.plot() # or you can use backtest.history to analyze data

Congratulations! Now you have the results of your strategy backtest on the real UniV3 data!