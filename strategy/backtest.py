"""
``backtest`` contains classes to define investing strategy and backtest it against real data.

Example::

    from strategy.primitives import Frequency, Pool, Token
    from strategy.backtest import Backtest, AbstractStrategy

    class Strategy(AbstractStrategy):        
        def rebalance(
            self,
            t: datetime,
            c: float,
            vol: float,
            l: Callable[[float], float],
            pool_data: PoolData,
        ) -> bool:
            if not self.portfolio.position("main"):
                self.portfolio.add_position(Position(id="main", a = c / 2, b = c * 2))
                pos = self.portfolio.position("main")
                pos.deposit(c, 1)
            return False

    strategy = Strategy()
    backtest = Backtest(strategy)
    backtest.run_for_pool(Pool(Token.WBTC, Token.USDC, Fee.MIDDLE), Frequency.DAY, 0.001)
    backtest.plot()

"""

from datetime import datetime

from pandas.core.frame import DataFrame
from strategy.primitives import Frequency, Pool
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

    The list of tracked values:

    - `c` - Current price
    - `l` - Current virtual liquidity for the position
    - `al` - Current active virtual liquidity for the position (i.e. taking into account if price is out of bounds)
    - `pool_fee` - Current fee distributes in the UniV3 pool
    - `pool_fees` - Accumulated to date fees distributes in the UniV3 pool
    - `pool_l` - Current virtual liquidity for the pool
    - `y` - value of the position denominated in ``Y`` token
    - `net_y` - `value of the position + accumulated fees - rebalance costs` denominated in ``Y`` token
    - `a` - Left bound of liquidity interval (price)
    - `b` - Right bound of liquidity interval (price)
    - `fee` - Fee earned by the position
    - `fees` - Accunulated fees earned by the position
    - `cost` - Rebalance costs for the position
    - `costs` - Accumulated rebalance costs for the position

    Note: The convention is to keep cost at portfolio level (thus in PortfolioHistory)

    :param pos: The position to track
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
            "net_y",
            "fee",
            "fees",
            "cost",
            "costs",
            "il",
        ]
        self._data = pd.DataFrame([], columns=self.cols)
        self.pool_fees = 0
        self.costs = 0

    @property
    def data(self) -> pd.DataFrame:
        """
        Historical data
        """
        return self._data

    def snapshot(
        self, t: datetime, c: float, pool_fee: float, pool_l: float, cost: float
    ):
        """
        Write current state

        :param t: Time for state snapshot
        :param c: Price at time ``t``
        :param pool_fee: Total fees distributed in the UniV3 pool in the current period(denominated in ``Y`` token)
        :param pool_l: Total liquidity in the UniV3 pool at time ``t``
        :param cost: Rebalance cost
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

    def plot(self, sizex=20, sizey=10):
        """
        Plot historical data

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
        axes[2, 1].set_title("Y value + accumulated fees - costs")
        axes[3, 0].plot(self._data["pool_fees"], color=COLORS["fee"])
        axes[3, 0].set_title("Pool fees")
        axes[3, 1].plot(self._data["fees"], color=COLORS["fee"])
        axes[3, 1].set_title("Earned fees")
        axes[4, 0].plot(self._data["fees"].cumsum(), color=COLORS["fee"])
        axes[4, 0].set_title("Accumulated fees")
        axes[4, 1].plot(self._data["il"], color=COLORS["il"])
        axes[4, 1].set_title("Impermanent loss")
        axes[5, 0].plot(self._data["cost"], color=COLORS["cost"])
        axes[5, 0].set_title("Current cost")
        axes[5, 1].plot(self._data["costs"], color=COLORS["cost"])
        axes[5, 1].set_title("Accumulated costs")

        for x in range(6):
            for y in range(2):
                axes[x, y].tick_params(axis="x", labelrotation=45)


class PortfolioHistory(PositionHistory):
    """
    ``PortfolioHistory`` tracks portfolio values over time.
    Each time ``snapshot`` method is called it remembers current state in time.
    All tracked values then can be accessed via ``data`` method that will return a ``pandas`` Dataframe.
    Or can be plotted using ``plot`` method.

    The list of tracked values:

    - `c` - Current price
    - `l` - Current virtual liquidity for the portfolio
    - `al` - Current active virtual liquidity for the portfolio (i.e. taking into account if price is out of bounds)
    - `pool_fee` - Current fee distributes in the UniV3 pool
    - `pool_fees` - Accumulated to date fees distributes in the UniV3 pool
    - `pool_l` - Current virtual liquidity for the pool
    - `y` - value of the portfolio denominated in ``Y`` token
    - `net_y` - `value of the portfolio + accumulated fees - rebalance costs` denominated in ``Y`` token
    - `a` - Left bound of liquidity interval (price)
    - `b` - Right bound of liquidity interval (price)
    - `fee` - Fee earned by the portfolio
    - `fees` - Accunulated fees earned by the portfolio
    - `cost` - Rebalance costs for the portfolio
    - `costs` - Accumulated rebalance costs for the portfolio

    Note: The convention is to keep cost at portfolio level (thus in PortfolioHistory)

    :param portfolio: The portfolio to track
    """

    def __init__(self, portfolio: Portfolio):
        self._portfolio = portfolio
        self._portfolio_history = PositionHistory(portfolio)
        self._positions_history = {}

    @property
    def data(self) -> pd.DataFrame:
        """
        Historical data
        """
        return self._portfolio_history.data

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

    def plot(self, sizex=20, sizey=10, with_positions: bool = False):
        self._portfolio_history.plot(sizex, sizey)
        if not with_positions:
            return
        for pos in self._positions_history.values():
            pos.plot(sizex, sizey)


class AbstractStrategy:
    """
    ``AbstractStrategy`` is a base class for defining a strategy.

    When backtested, ``Backtest`` class runs through all data and calls the ``rebalance`` method.
    That is the only method that needs to be implemented by the actual Strategy.

    Example::

        class RabalanceStrategy(AbstractStrategy):
            def rebalance(
                self,
                t: datetime,
                c: float,
                vol: float,
                l: Callable[[float], float],
                pool_data: PoolData,
            ) -> bool:
                # Lazy init code
                if not self.portfolio.position("main"):
                    self.portfolio.add_position(Position(id="main", a = c / 2, b = c * 2))
                    pos = self.portfolio.position("main")
                    pos.deposit(c, 1)
                    self.c0 = c

                # Rebalance code
                if abs(c0 / c - 1) > 0.25:
                    pos.set_a(c / 2, c)
                    pos.set_b(c * 2, c)
                    self.c0 = c
                    return True

                return False

    A typical definition of a ``rebalance`` method would contain two sections:

    - `Lazy init`
                  On the first call you need to initialize strategy's portfolio under management.
                  Here you need to create initial positions with ``add_position`` method and invest initial amount using ``deposit`` method.
    - `Rebalance`
                  In this section you decied if you want to rebalance or not.
                  If you rebalance you need to return ``True`` from the rebalance method to account for rebalance costs
    """

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
        """
        ``rebalance`` method defines how the strategy will be initialized and rebalanced.
        See :ref:`class AbstractStrategy` description for details

        :param t: Current time
        :param c: Current price
        :param vol: Current volume
        :param l: Current liquidity distribution function (depending on price)
        :param pool_data: All historical data used for extra logic. See :ref:`class PoolData` for more.
        :return: ``True`` if the rebalance happened, ``False`` otherwise
        """
        raise NotImplemented

    @property
    def portfolio(self):
        """
        Portfolio of the strategy
        """
        return self._portfolio


class Backtest:
    """
    ``Backtest`` is used for backtesting strategy on pool data.
    It contains the logic of running strategy thrhough the data and tracks results.

    :param strategy: Strategy to backtest
    """

    def __init__(self, strategy_factory: Callable[[], AbstractStrategy]):
        self._strategy = strategy_factory()
        self._history = None

    def run(self, pool_data: PoolData, rebalance_cost_y: float):
        """
        :param pool_data: Data to run strategy on
        :param rebalance_cost_y: The cost of each rebalance
        """
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
                pool_data[:prev_t],
            )

            cost = rebalance_cost_y if rebalance else 0
            c = data["c"][t]
            pool_fee = data["fee"][t]
            pool_l = pool_data.liquidity(t, c)
            self._strategy.portfolio.charge_fees(c, pool_l, pool_fee)
            self._history.snapshot(t, c, pool_fee, pool_l, cost)
            self._strategy.portfolio.reinvest_fees(c)

    def run_for_pool(self, pool: Pool, freq: Frequency, rebalance_cost_y: float):
        """
        Download the data and backtest strategy

        :param pool: Pool to test on
        :param freq: Resampling frequence. See :ref:`class Frequency`
        :param rebalance_cost_y: The cost of each rebalance
        """
        pool_data = PoolData.from_pool(pool, freq)
        self.run(pool_data, rebalance_cost_y)

    @property
    def history(self) -> DataFrame:
        """
        Results of the run. If run was not called before this property ``Exception`` will be raised.
        See :ref:`class PositionHistory` for data contents.
        """
        if not self._history:
            raise Exception("Please call `run` method first")
        return self._history.data

    def plot(self, sizex: int = 20, sizey: int = 50, with_positions: bool = False):
        """
        Plot results of the run. If run was not called before this property ``Exception`` will be raised.

        :param sizex: `x` size of one chart
        :param sizey: `y` size of one chart
        """
        if not self._history:
            raise Exception("Please call `run` method first")
        self._history.plot(sizex=sizex, sizey=sizey, with_positions=with_positions)
