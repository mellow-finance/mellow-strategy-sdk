from abc import ABC, abstractmethod
import pandas as pd

from .Portfolio import Portfolio
from .Data import PoolDataUniV3


class AbstractStrategy:
    def __init__(self, portfolio: Portfolio = None):
        self.portfolio = Portfolio('main')
        if portfolio is not None:
            self.portfolio = portfolio

    def rebalance(self, *args, **kwargs) -> None:
        raise Exception(NotImplemented)

    def snapshot(self, price: float) -> None:
        raise Exception(NotImplemented)


class Backtest:
    def __init__(self, strategy: AbstractStrategy):
        self.strategy = strategy

    def backtest(self, pool_data: PoolDataUniV3, start_day=None, end_date=None):
        df_swaps = pool_data.swaps
        if start_day is None:
            start_day = df_swaps.index.min().normalize()
        if end_date is None:
            end_date = df_swaps.index.max().normalize()

        time_range = list(pd.date_range(start=start_day, end=end_date))

        for i in range(1, len(time_range)):
            left, right = time_range[i - 1], time_range[i]
            df_swap_introday_slice = df_swaps[left:right]
            for idx, row in df_swap_introday_slice.iterrows():
                self.strategy.rebalance(timestamp=idx, row=row)

            self.strategy.snapshot(row['price'])

