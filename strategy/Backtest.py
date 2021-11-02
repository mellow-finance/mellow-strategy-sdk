from .Strategies import AbstractStrategy
from .Portfolio import Portfolio
from .History import PortfolioHistory


class Backtest:
    def __init__(self,
                 strategy: AbstractStrategy,
                 portfolio: Portfolio = None):

        self.strategy = strategy
        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio


    def backtest(self, df_swaps) -> PortfolioHistory:
        history_tracker = PortfolioHistory()

        for idx, row in df_swaps.iterrows():
            # df_swaps_prev = df_swaps[:idx]
            self.strategy.rebalance(timestamp=idx, row=row, portfolio=self.portfolio)
            snapshot = self.portfolio.snapshot(idx, row['price'])
            history_tracker.add_snapshot(snapshot)

        return history_tracker
