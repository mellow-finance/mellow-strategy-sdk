from abc import ABC, abstractmethod

from .Portfolio import Portfolio
from .PortfolioHistory import PortfolioHistory


class AbstractStrategy(ABC):
    def __init__(self, portfolio: Portfolio = None):
        self.portfolio = Portfolio('main')
        if portfolio is not None:
            self.portfolio = portfolio

    @abstractmethod
    def rebalance(self, *args, **kwargs) -> None:
        raise Exception(NotImplemented)

    @abstractmethod
    def snapshot(self, date, price: float) -> dict:
        raise Exception(NotImplemented)


class Backtest:
    def __init__(self, strategy: AbstractStrategy):
        self.strategy = strategy

    def backtest(self, df_swaps) -> PortfolioHistory:
        history_tracker = PortfolioHistory()

        for idx, row in df_swaps.iterrows():
            df_swaps_prev = None #df_swaps[:idx]
            self.strategy.rebalance(timestamp=idx, row=row, prev_swaps=df_swaps_prev)
            snapshot = self.strategy.snapshot(idx, row['price'])
            history_tracker.add_snapshot(snapshot)

        return history_tracker
