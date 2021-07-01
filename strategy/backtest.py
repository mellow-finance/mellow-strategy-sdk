"""
``history`` module models Portfolio and Position spanning over time
"""

from datetime import datetime
from decimal import Decimal
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
            "fee",
            "fees",
            "y_and_fees",
            "a",
            "b",
            "il",
            "c",
            "fee_per_l",
        ]
        self._data = pd.DataFrame([], columns=self.cols)

    def snapshot(self, t: datetime, c: Decimal, fee_per_l: Decimal):
        """
        Write current state

        :param t: Time for state snapshot
        :param c: Price at time ``t``
        :param fee_per_l: Total fees at Uniswap V3 pool per total liquidity at time ``t``
        """
        self._data.loc[t] = [np.nan] * len(self.cols)
        self._data["c"][t] = c
        self._data["fee_per_l"][t] = fee_per_l
        self._data["l"][t] = self._pos.l
        self._data["al"][t] = self._pos.active_l(c)
        self._data["y"][t] = self._pos.y(c)
        self._data["a"][t] = self._pos.a()
        self._data["b"][t] = self._pos.b()
        self._data["il"][t] = self._pos.il(c)
        fee = self._pos.active_l(c) * fee_per_l
        self._data["fee"][t] = fee
        self._data["y_and_fees"][t] = self.data["y"][t] + self.fees

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
        axes[0, 0].plot(self.data["c"], color="#00bb00")
        axes[0, 0].plot(self.data["a"], color="#0000bb")
        axes[0, 0].plot(self.data["b"], color="#0000bb")
        axes[0, 0].set_title("Price and bounds")
        axes[0, 1].plot(self.data["fee_per_l"], color="#777777")
        axes[0, 1].set_title("Fee per liquidity unit")
        axes[1, 0].plot(self.data["al"], color="#0000bb")
        axes[1, 0].set_title("Active liquidity")
        axes[1, 1].plot(self.data["l"], color="#0000bb")
        axes[1, 1].set_title("Liquidity")
        axes[2, 0].plot(self.data["y"], color="#0000bb")
        axes[2, 0].set_title("Y value")
        axes[2, 1].plot(self.data["y_and_fees"], color="#0000bb")
        axes[2, 1].set_title("Y value + fees")
        axes[3, 0].plot(self.data["fee"], color="#0000bb")
        axes[3, 0].set_title("Current fees")
        axes[3, 1].plot(self.data["fees"], color="#0000bb")
        axes[3, 1].set_title("Accumulated fees")
        axes[4, 0].plot(self.data["il"], color="#0000bb")
        axes[4, 0].set_title("Impermanent loss")


class PortfolioHistory:
    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._portfolio_history = PositionHistory(portfolio)
        self._positions_history = {}

    def snapshot(self, t, price, fee_per_l):
        self._portfolio_history.snapshot(t, price, fee_per_l)
        for id in self._portfolio.position_ids():
            pos = self.position(id)
            if id not in self._positions_history:
                self._positions_history[id] = PositionHistory(pos)
            hist = self._positions_history[id]
            hist.snapshot(price, fee_per_l)

    def plot(self, sizex=20, sizey=10):
        self._portfolio_history.plot(sizex, sizey)
        for pos in self._positions_history.values():
            pos.plot(sizex, sizey)


class Backtest:
    def __init__(self, strategy: AbstractStrategy):
        self._strategy = strategy
        self._history = None

    def run(self, pool_data: PoolData):
        portfolio = self._strategy.portfolio()
        self._history = PortfolioHistory(portfolio)

        data = pool_data.data()
        fee = Decimal(pool_data.pool().fee().value) / 100000
        for t in data.index:
            self._strategy.rebalance(
                t, data["c"], data["vol0"] * fee, data["vol1"] * fee
            )
            c = data["c"][t]
            fee0 = data["vol0"][t] * fee
            fee1 = data["vol1"][t] * fee
            fee = fee0 * c + fee1
            l = pool_data.liquidity(t, c)
            fee_per_l = fee / l
            self._history.snapshot(t, c, fee_per_l)

    def history(self):
        return self._history

    def plot(self, sizex=20, sizey=10):
        if not self._history:
            raise Exception("Please call `run` method first")
        self._history.plot(sizex=sizex, sizey=sizey)
