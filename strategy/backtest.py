import copy
from typing import Tuple
import pandas as pd
import numpy as np
import polars as pl

from strategy.strategies import AbstractStrategy
from strategy.portfolio import Portfolio
from strategy.history import PortfolioHistory, RebalanceHistory, UniPositionsHistory

from strategy.utils import Singleton, AtomicSnapshot

class Backtest:
    """
    | ``Backtest`` emulate portfolio behavior on historical data.
    | Collects and process portfolio state for each point in time.
    | Returns in a convenient form for analyzing the results
    """
    def __init__(self,
                 strategy: AbstractStrategy,
                 portfolio: Portfolio = None,
                 ):

        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio

        self.strategy = strategy

    def backtest(self, df: pl.DataFrame) -> Tuple[PortfolioHistory, RebalanceHistory, UniPositionsHistory]:
        """
        | 1) Sends ``Portfolio`` and every market action to ``AbstractStrategy.rebalance``
        | 2) expected return of ``AbstractStrategy.rebalance`` is name of strategy action e.g.
        | 'init', 'rebalance', 'stop', 'some_cool_action', None. When there is no strategy action prefer return None.
        | Add porfolio action to ``RebalanceHistory``
        | 3) Add Porfolio snapshot to ``PortfolioHistory``
        | 4) Add Porfolio snapshot to ``UniPositionsHistory``
        |
        | You can send anything you want to ``AbstractStrategy.rebalance`` cause it take *args, **kwargs,
        | but be sure to send raw=[('timestamp', 'price')] and portfolio=self.portfolio

        Attributes:
            df_swaps: df with pool swaps, or df with market data. df format is [('timestamp', 'price')]

        Returns:
            | History classes that store accumulated&processed results of backtesting.
            |
            | ``PortfolioHistory`` - keeps metrics such as APY
            | ``RebalanceHistory`` - keeps information about portfolio actions, such as init ot rebalances
            | ``UniPositionsHistory`` -  keeps information about open UniV3 positions
        """

        portfolio_history = PortfolioHistory()
        rebalance_history = RebalanceHistory()
        uni_history = UniPositionsHistory()

        ats = AtomicSnapshot() # new PortfolioHistory
        ats.portfolio = self.portfolio
        ats.snapshots = []

        for record in df.to_dicts():
            ats.timestamp = record['timestamp']
            ats.price = record['price']

            is_rebalanced = self.strategy.rebalance(record=record, portfolio=self.portfolio)
            portfolio_snapshot = self.portfolio.snapshot(record['timestamp'], record['price'])
            portfolio_history.add_snapshot(portfolio_snapshot)
            rebalance_history.add_snapshot(record['timestamp'], is_rebalanced)
            uni_history.add_snapshot(record['timestamp'], copy.copy(self.portfolio.positions))

        return portfolio_history, rebalance_history, uni_history
