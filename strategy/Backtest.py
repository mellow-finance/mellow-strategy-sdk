from .Strategies import AbstractStrategy
from .Portfolio import Portfolio
from .History import PortfolioHistory, RebalanceHistory

from typing import Tuple


class Backtest:
    """
        ``Backtest`` is used for backtesting strategy on pool data.
        It contains the logic of running strategy thrhough the data and tracks results.
        :param strategy: Strategy to backtest
        :param portfolio: Portfolio to manage
    """
    def __init__(self,
                 strategy: AbstractStrategy,
                 portfolio: Portfolio = None):

        self.strategy = strategy
        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio

    def backtest(self, df_swaps) -> Tuple[PortfolioHistory, RebalanceHistory]:
        portfolio_history = PortfolioHistory()
        rebalance_history = RebalanceHistory()

        for idx, row in df_swaps.iterrows():
            df_swaps_prev = df_swaps[:idx]
            is_rebalanced = self.strategy.rebalance(timestamp=idx, row=row, prev_data=df_swaps_prev, portfolio=self.portfolio)
            portfolio_snapshot = self.portfolio.snapshot(idx, row['price'])
            portfolio_history.add_snapshot(portfolio_snapshot)
            rebalance_history.add_snapshot(idx, is_rebalanced)

        return portfolio_history, rebalance_history
