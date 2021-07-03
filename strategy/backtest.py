"""
``history`` module models Portfolio and Position spanning over time
"""

from datetime import datetime
from typing import Optional
from strategy.data import PoolData
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from strategy.portfolio import AbstractStrategy, Position, Portfolio


class PositionHistory:
    """
    ``PositionHistory`` tracks position values over time.
    Each time ``snapshot`` method is called it remembers current state in time.
    All tracked values then can be accessed via ``data`` method that will return a ``pandas`` Dataframe.
    Or can be plotted using ``plot`` method.
    """

    def __init__(self, pos: Position):
        self._pos = pos
        self.cols = [
            "l",
            "al",
            "y",
            "pool_fee",
            "pool_fees",
            "fee",
            "fees",
            "y_and_fees",
            "a",
            "b",
            "il",
            "c",
            "pool_l",
        ]
        self._data = pd.DataFrame([], columns=self.cols)
        self.fees = 0
        self.pool_fees = 0

    def snapshot(self, t: datetime, c: float, pool_fee: float, pool_l: float):
        """
        Write current state

        :param t: Time for state snapshot
        :param c: Price at time ``t``
        :param fee: Fees for the current period denominated in ``Y`` token
        :param pool_l: Total liquidity in the pool at time ``t``
        """
        if t in self._data.index:
            return
        self._data.loc[t] = [np.nan] * len(self.cols)
        self._data["c"][t] = c
        self._data["pool_l"][t] = pool_l
        self._data["pool_fee"][t] = pool_fee
        self._data["l"][t] = self._pos.l
        self._data["al"][t] = self._pos.active_l(c)
        self._data["y"][t] = self._pos.y(c)
        self._data["a"][t] = self._pos.a
        self._data["b"][t] = self._pos.b
        self._data["il"][t] = self._pos.il(c)
        l = self._pos.active_l(c)
        total_l = l + pool_l
        fee = 0
        if total_l != 0:
            fee = l * pool_fee / total_l
        self._data["fee"][t] = fee
        self.fees += fee
        self.pool_fees += pool_fee
        self._data["fees"][t] = self.fees
        self._data["pool_fees"][t] = self.pool_fees
        self._data["y_and_fees"][t] = self._data["y"][t] + self._data["fees"][t]

    @property
    def data(self) -> pd.DataFrame:
        """
        Tracking data

        The list of tracked values:

        - `a` - Left bound of liquidity interval (price)
        - `b` - Right bound of liquidity interval (price)
        - `c` - Current price
        - `fee_per_l` - fees that could ber earned available per unit of liquidity at current time
        - `l` - Liquidity of the position
        - `al` - Active liquidity of the position (i.e. `l` when `c` is in (a, b), 0 o/w)
        - `fee` - fee earned at current time
        - `fees` - cumulative fees earned at current time
        - `y` - value of the position denominated in ``Y`` token
        - `y_and_fees` - `y` + `fees`
        """
        return self._data

    def plot(self, sizex=20, sizey=10):
        """
        Plot tracking data

        :param sizex: `x` size of one chart
        :param sizey: `y` size of one chart
        """
        fig, axes = plt.subplots(5, 2, figsize=(sizex, sizey))
        fig.suptitle(
            f"Stats for {self._pos.id}",
            fontsize=16,
        )
        axes[0, 0].plot(self._data["c"], color="#00bb00")
        axes[0, 0].plot(self._data["a"], color="#0000bb")
        axes[0, 0].plot(self._data["b"], color="#0000bb")
        axes[0, 0].tick_params(axis="x", labelrotation=45)
        axes[0, 0].set_title("Price and bounds")
        axes[0, 1].plot(self._data["pool_fees"], color="#777777")
        axes[0, 1].set_title("Pool fees")
        axes[1, 0].plot(self._data["pool_l"], color="#00bbbb")
        axes[1, 0].set_title("Pool liquidity")
        axes[1, 1].plot(self._data["al"], color="#00bbbb")
        axes[1, 1].set_title("Active liquidity")
        axes[2, 0].plot(self._data["y"], color="#0000bb")
        axes[2, 0].set_title("Y value")
        axes[2, 1].plot(self._data["y_and_fees"], color="#0000bb")
        axes[2, 1].set_title("Y value + fees")
        axes[3, 0].plot(self._data["fee"], color="#0000bb")
        axes[3, 0].set_title("Current fees")
        axes[3, 1].plot(self._data["fees"], color="#0000bb")
        axes[3, 1].set_title("Accumulated fees")
        axes[4, 0].plot(self._data["il"], color="#bb00bb")
        axes[4, 0].set_title("Impermanent loss")
        axes[4, 1].plot(self._data["l"], color="#00bbbb")
        axes[4, 1].set_title("Liquidity")

        for x in range(5):
            for y in range(2):
                axes[x, y].tick_params(axis="x", labelrotation=45)


class PortfolioHistory:
    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._portfolio_history = PositionHistory(portfolio)
        self._positions_history = {}

    def snapshot(self, t: datetime, c: float, pool_fee: float, pool_l: float):
        self._portfolio_history.snapshot(t, c, pool_fee, pool_l)
        for id in self._portfolio.position_ids:
            pos = self._portfolio.position(id)
            if id not in self._positions_history:
                self._positions_history[id] = PositionHistory(pos)
            hist = self._positions_history[id]
            hist.snapshot(t, c, pool_fee, pool_l)

    def plot(self, sizex=20, sizey=10):
        self._portfolio_history.plot(sizex, sizey)
        for pos in self._positions_history.values():
            pos.plot(sizex, sizey)


class Backtest:
    def __init__(self, strategy: AbstractStrategy):
        self._strategy = strategy
        self._history = None

    def run(self, pool_data: PoolData):
        portfolio = self._strategy.portfolio
        self._history = PortfolioHistory(portfolio)

        data = pool_data.data
        fee = float(pool_data.pool.fee.value) / 100000
        index = data.index
        for i in range(1, len(index)):
            t = index[i]
            prev_t = index[i - 1]
            self._strategy.rebalance(
                prev_t,
                data["c"][prev_t],
                data["vol"][prev_t],
                lambda c: pool_data.liquidity(prev_t, c),
                pool_data,
            )
            c = data["c"][t]
            fee = data["fee"][t]
            l = pool_data.liquidity(t, c)
            # print(fee, l, c, prev_t)
            self._history.snapshot(t, c, fee, l)

    @property
    def history(self):
        return self._history

    def plot(self, sizex=20, sizey=10):
        if not self._history:
            raise Exception("Please call `run` method first")
        self._history.plot(sizex=sizex, sizey=sizey)
