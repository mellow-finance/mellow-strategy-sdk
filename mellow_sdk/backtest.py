import copy
from typing import Tuple
import polars as pl

from mellow_sdk.strategies import AbstractStrategy
from mellow_sdk.portfolio import Portfolio
from mellow_sdk.history import PortfolioHistory, RebalanceHistory, UniPositionsHistory


class Backtest:
    """
    | ``Backtest`` emulate portfolio behavior on historical data.
    | Collects and process portfolio state for each event in historical data.
    | Returns in a convenient form for analyzing the results
    """
    def __init__(
        self,
        strategy: AbstractStrategy,
        portfolio: Portfolio = None,
    ) -> None:

        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio

        self.strategy = strategy

    def backtest(
            self,
            df: pl.DataFrame
    ) -> Tuple[PortfolioHistory, RebalanceHistory, UniPositionsHistory]:
        """
        | 1) Calls ``AbstractStrategy.rebalance`` for every market action with.
        | 2) The return of ``AbstractStrategy.rebalance`` is a name of strategy action e.g.
        | 'init', 'rebalance', 'stop', 'some_cool_action', None. When there is no strategy action ``rebalance`` returns None.
        | 3) Add Strategy action to ``RebalanceHistory``
        | 4) Add Porfolio snapshot to ``PortfolioHistory``
        | 5) Add Porfolio snapshot to ``UniPositionsHistory``
        |
        | You can call ``AbstractStrategy.rebalance`` with any arguments, as it takes *args, **kwargs.
        | Note that 'timestamp', 'price' and 'portfolio' is required.

        Attributes:
            df: df with pool events, or df with market data. df format is [('timestamp': datetime, 'price' : float)]

        Returns:
            | History classes that store different portfolio stapshots.
            |
            | ``PortfolioHistory`` - keeps portfolio snapshots such as: value, fees, etc.
            | ``RebalanceHistory`` - keeps strategy actions, such as init ot rebalances.
            | ``UniPositionsHistory`` -  keeps information about opened UniV3 positions.
        """
        portfolio_history = PortfolioHistory()
        rebalance_history = RebalanceHistory()
        uni_history = UniPositionsHistory()
        for record in df.to_dicts():
            is_rebalanced = self.strategy.rebalance(record=record, portfolio=self.portfolio)
            portfolio_snapshot = self.portfolio.snapshot(record['timestamp'], record['price'])
            portfolio_history.add_snapshot(portfolio_snapshot)
            rebalance_history.add_snapshot(record['timestamp'], is_rebalanced)
            uni_history.add_snapshot(record['timestamp'], copy.copy(self.portfolio.positions))

        return portfolio_history, rebalance_history, uni_history
