"""
``history`` module models Portfolio and Position spanning over time

class PositionHistory
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: PositionHistory
    :members:
"""

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
        self._data = pd.DataFrame([], cols=self.cols, index=pd.DatetimeIndex())
        self.fees = 0

    def snapshot(self, t, price, fee_per_l):
        self._data.loc[t] = [np.nan] * len(self.cols)
        self._data["c"][t] = price
        self._data["fee_per_l"][t] = fee_per_l
        self._data["l"][t] = self.pos.l
        self._data["al"][t] = self.pos.active_l(price)
        self._data["y"][t] = self.pos.y(price)
        self._data["a"][t] = self.pos.a()
        self._data["b"][t] = self.pos.b()
        self._data["il"][t] = self.pos.il(price)
        fee = self.pos.active_l(price) * fee_per_l
        self.fees += fee
        self._data["fee"][t] = fee
        self._data["fees"][t] = self.fees
        self._data["y_and_fees"][t] = self.data["y"][t] + self.fees

    def data(self):
        return self._data

    def plot(self, sizex=20, sizey=10):
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


class PortfolioHistory(PositionHistory):
    def __init__(self, portfolio: Portfolio, index: pd.Index):
        self._portfolio_history = PositionHistory(portfolio, index)
        self._position_history = [
            PortfolioHistory(pos, index) for pos in portfolio.positions()
        ]

    def snapshot(self, t, price, fee_per_l):
        self._position.snapshot(t, price, fee_per_l)
        for pos in self._positions:
            pos.snapshot(t, price, fee_per_l)

    def plot(self, sizex=20, sizey=10):
        self._position.plot(sizex, sizey)
        for pos in self._positions:
            pos.plot(sizex, sizey)
