"""
``history`` module models Portfolio and Position spanning over time
"""

from datetime import datetime
from strategy.const import COLORS
from typing import Callable, Optional
from strategy.data import PoolData
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from strategy.portfolio import Position, Portfolio


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
            "c",
            "l",
            "al",
            "pool_fee",
            "pool_fees",
            "pool_l",
            "a",
            "b",
            "y",
            "fee",
            "fees",
            "cost",
            "costs",
            "il",
            "net_y",
        ]
        self._data = pd.DataFrame([], columns=self.cols)
        self.pool_fees = 0
        self.costs = 0

    def snapshot(
        self, t: datetime, c: float, pool_fee: float, pool_l: float, cost: float
    ):
        """
        Write current state

        :param t: Time for state snapshot
        :param c: Price at time ``t``
        :param fee: Fees for the current period denominated in ``Y`` token
        :param pool_l: Total liquidity in the pool at time ``t``
        """
        if t in self._data.index:
            return
        self.pool_fees += pool_fee
        self.costs += cost
        self._data.loc[t] = [np.nan] * len(self.cols)
        self._data["c"][t] = c
        self._data["pool_l"][t] = pool_l
        self._data["pool_fee"][t] = pool_fee
        self._data["pool_fees"][t] = self.pool_fees
        self._data["l"][t] = self._pos.l
        self._data["al"][t] = self._pos.active_l(c)
        self._data["y"][t] = self._pos.y(c)
        self._data["a"][t] = self._pos.a
        self._data["b"][t] = self._pos.b
        self._data["il"][t] = self._pos.il(c)
        self._data["cost"][t] = cost
        self._data["costs"][t] = self.costs
        self._data["fees"][t] = self._pos.fees
        self._data["net_y"][t] = (
            self._data["y"][t] + self._data["fees"][t] - self._data["costs"][t]
        )

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
        fig, axes = plt.subplots(6, 2, figsize=(sizex, sizey))
        fig.suptitle(
            f"Stats for {self._pos.id}",
            fontsize=16,
        )
        axes[0, 0].plot(self._data["c"], label="c", color=COLORS["c"])
        axes[0, 0].plot(self._data["a"], ":", label="a", color=COLORS["c"])
        axes[0, 0].plot(self._data["b"], ":", label="b", color=COLORS["c"])
        axes[0, 0].set_title("Price and bounds")
        axes[0, 0].legend()
        axes[0, 1].plot(self._data["l"], color=COLORS["l"])
        axes[0, 1].set_title("Position liquidity")

        axes[1, 0].plot(self._data["pool_l"], color=COLORS["l"])
        axes[1, 0].set_title("Pool liquidity")
        axes[1, 1].plot(self._data["al"], color=COLORS["l"])
        axes[1, 1].set_title("Active liquidity")
        axes[2, 0].plot(self._data["y"], color=COLORS["y"])
        axes[2, 0].set_title("Y value")
        axes[2, 1].plot(self._data["net_y"], color=COLORS["y"])
        axes[2, 1].set_title("Y value + Accumulated fees - costs")
        axes[3, 0].plot(self._data["fees"].diff(), color=COLORS["fee"])
        axes[3, 0].set_title("Current fees")
        axes[3, 1].plot(self._data["fees"], color=COLORS["fee"])
        axes[3, 1].set_title("Accumulated fees")
        axes[4, 0].plot(self._data["cost"], color=COLORS["cost"])
        axes[4, 0].set_title("Current cost")
        axes[4, 1].plot(self._data["costs"], color=COLORS["cost"])
        axes[4, 1].set_title("Accumulated costs")
        axes[5, 0].plot(self._data["il"], color=COLORS["il"])
        axes[5, 0].set_title("Impermanent loss")
        axes[5, 1].plot(self._data["pool_fees"], color=COLORS["fee"])
        axes[5, 1].set_title("Pool fees")

        for x in range(6):
            for y in range(2):
                axes[x, y].tick_params(axis="x", labelrotation=45)


class PortfolioHistory:
    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._portfolio_history = PositionHistory(portfolio)
        self._positions_history = {}

    def snapshot(
        self, t: datetime, c: float, pool_fee: float, pool_l: float, cost: float
    ):
        self._portfolio_history.snapshot(t, c, pool_fee, pool_l, cost)
        for id in self._portfolio.position_ids:
            pos = self._portfolio.position(id)
            if id not in self._positions_history:
                self._positions_history[id] = PositionHistory(pos)
            hist = self._positions_history[id]
            hist.snapshot(t, c, pool_fee, pool_l, 0)

    def plot(self, sizex=20, sizey=10):
        self._portfolio_history.plot(sizex, sizey)
        for pos in self._positions_history.values():
            pos.plot(sizex, sizey)


class AbstractStrategy:
    def __init__(self):
        self._portfolio = Portfolio()

    def rebalance(
        self,
        t: datetime,
        c: float,
        vol: float,
        l: Callable[[float], float],
        pool_data: PoolData,
    ) -> bool:
        raise NotImplemented

    @property
    def portfolio(self):
        return self._portfolio


class Backtest:
    def __init__(self, strategy: AbstractStrategy):
        self._strategy = strategy
        self._history = None

    def run(self, pool_data: PoolData, rebalance_cost_y: float):
        portfolio = self._strategy.portfolio
        self._history = PortfolioHistory(portfolio)

        data = pool_data.data
        index = data.index
        for i in range(1, len(index)):
            t = index[i]
            prev_t = index[i - 1]
            rebalance = self._strategy.rebalance(
                prev_t,
                data["c"][prev_t],
                data["vol"][prev_t],
                lambda c: pool_data.liquidity(prev_t, c),
                pool_data,
            )

            cost = rebalance_cost_y if rebalance else 0
            c = data["c"][t]
            pool_fee = data["fee"][t]
            pool_l = pool_data.liquidity(t, c)
            print(self._strategy.portfolio.charge_fees(c, pool_l, pool_fee))
            self._history.snapshot(t, c, pool_fee, pool_l, cost)
            self._strategy.portfolio.reinvest_fees(c)

    @property
    def history(self):
        return self._history

    def plot(self, sizex=20, sizey=10):
        if not self._history:
            raise Exception("Please call `run` method first")
        self._history.plot(sizex=sizex, sizey=sizey)
