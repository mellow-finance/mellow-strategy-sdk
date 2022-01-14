from strategy.strategies import AbstractStrategy
from strategy.portfolio import Portfolio
from strategy.history import PortfolioHistory, RebalanceHistory, UniPositionsHistory

from typing import Tuple
import pandas as pd
import copy


class Backtest:
    """
    ``Backtest`` is used for backtesting strategy on pool data.

    It contains the logic of running strategy on the market data and tracks results.

    Attributes:
        strategy: Strategy to backtest.
        portfolio: Portfolio to manage.
    """
    def __init__(self,
                 strategy: AbstractStrategy,
                 portfolio: Portfolio = None):

        self.strategy = strategy
        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio

    def backtest(
            self,
            df_swaps: pd.DataFrame
        ) -> Tuple[PortfolioHistory, RebalanceHistory, UniPositionsHistory]:
        """
        Run backtest on data.

        Args:
            df_swaps: UniswapV3 exchanges data frame.

        Returns:
            Portfolio statistics on historical data.
        """
        portfolio_history = PortfolioHistory()
        rebalance_history = RebalanceHistory()
        uni_history = UniPositionsHistory()

        for idx, row in df_swaps.iterrows():
            df_swaps_prev = df_swaps[['price']][:idx]
            is_rebalanced = self.strategy.rebalance(timestamp=idx, row=row, prev_data=df_swaps_prev, portfolio=self.portfolio)
            portfolio_snapshot = self.portfolio.snapshot(idx, row['price'])
            portfolio_history.add_snapshot(portfolio_snapshot)
            rebalance_history.add_snapshot(idx, is_rebalanced)
            uni_history.add_snapshot(idx, copy.copy(self.portfolio.positions))

        return portfolio_history, rebalance_history, uni_history
