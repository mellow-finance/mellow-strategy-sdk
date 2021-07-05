"""
``data`` module contains classes for getting and transforming the UniV3 data.

``RawData`` downloads external data. It can be used in notebooks for caching the downloaded data.

``PoolData`` is a wrapper around ``RawData`` that transforms, resamples data and makes it usable for backtesting.

Use ``PoolData`` by default and ``RawData`` if you want additional layer of customization.
"""

from __future__ import annotations
from strategy.const import COLORS
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from pandas.core.frame import DataFrame
from strategy.primitives import Pool, Token, Frequency
from decimal import Decimal
from datetime import datetime
from intervaltree import IntervalTree, Interval


class RawData:
    """
    ``RawData`` downloads external pool data.
    If for some reason you want to override host for data blobs use ``AWS_DATA_HOST`` env variable.

    Constructor is considered to be private, you want to use ``from_pool`` method to instantiate ``RawData``.
    """

    def __init__(
        self, swaps: pd.DataFrame, mints: pd.DataFrame, burns: pd.DataFrame, pool: Pool
    ):
        self._swaps = swaps
        self._mints = mints
        self._burns = burns
        self._pool = pool

    @classmethod
    def from_pool(cls: RawData, pool: Pool) -> RawData:
        """
        Create ``RawData`` for a specific pool

        :param pool: Pool specification
        :return: New ``RawData`` instance
        """
        print(f"Downloading swaps")
        swaps = pd.read_csv(
            RawData._get_download_url("swaps", pool),
            converters={
                "block_time": int,
                "block_number": int,
                "sqrt_price_x96": int,
                "amount0": int,
                "amount1": int,
                "liquidity": int,
            },
            parse_dates=["block_time"],
        )
        swaps.index = pd.to_datetime(swaps["block_time"], unit="s")
        print(f"Downloading burns")
        burns = pd.read_csv(
            RawData._get_download_url("burns", pool),
            converters={
                "block_time": int,
                "block_number": int,
                "tick_lower": int,
                "tick_upper": int,
                "amount": int,
                "amount0": int,
                "amount1": int,
            },
        )
        burns.index = pd.to_datetime(burns["block_time"], unit="s")
        print(f"Downloading mints")
        mints = pd.read_csv(
            RawData._get_download_url("mints", pool),
            converters={
                "block_time": int,
                "block_number": int,
                "tick_lower": int,
                "tick_upper": int,
                "amount": int,
                "amount0": int,
                "amount1": int,
            },
        )
        mints.index = pd.to_datetime(mints["block_time"], unit="s")
        print("Done")
        return cls(swaps, mints, burns, pool)

    @property
    def swaps(self) -> DataFrame:
        """
        Swap data
        """
        return self._swaps

    @property
    def mints(self) -> DataFrame:
        """
        Mints data
        """

        return self._mints

    @property
    def burns(self) -> DataFrame:
        """
        Burns data
        """
        return self._burns

    @property
    def pool(self) -> Pool:
        """
        Pool specification
        """
        return self._pool

    def _get_download_url(kind, pool: Pool):
        host = (
            os.getenv("AWS_DATA_HOST") or "mellow-uni-data.s3.us-east-2.amazonaws.com"
        )
        return f"https://{host}/{kind}-{pool.name}.csv"

    def __getitem__(self, items) -> RawData:
        return RawData(
            self._swaps.__getitem__(items),
            self._mints,  # don't cut the range, since we need data from the beginning
            self._burns,
            self._pool,
        )


class PoolData:
    """
    ``PoolData`` prepares data for backtesting. The data itself is available via ``data`` property as a ``pandas`` DataFrame with datetime index.
    All data is denominated in eth rather then wei (or btc rather that sat, etc.)
    The fields of the ``data`` are:

    - `c` - price
    - `c_inv` - 1 / `c`
    - `vol0` - amount of `token0` users swapped in the current period (i.e. only incoming part of the swap)
    - `vol1` - amount of `token1` users swapped in the current period (i.e. only incoming part of the swap)
    - `vol` - `vol0 * c + vol1` - total volume denominated in token ``Y``
    - `fee` -  Total fees distribtuted denominated in token ``Y``
    - `l` - average virtual liquidity used for swaps

    You can also use a subrange of data. Example::

        pool_data = PoolData.from_pool(...)
        p = pool_data["2021-06-25":"2021-06-27"]

    Constructor is considered to be private, you want to use ``from_pool`` or ``from_raw_Data`` method to instantiate ``RawData``.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        mints: pd.DataFrame,
        burns: pd.DataFrame,
        pool: Pool,
        freq: Frequency,
    ):
        self._data = data
        self._pool = pool
        self._freq = freq
        self._mints = mints
        self._burns = burns

    @classmethod
    def from_raw_data(cls: PoolData, raw_data: RawData, freq: Frequency) -> PoolData:
        """
        Create a PoolData from RawData

        :param raw_data: Raw downloaded data
        :param freq: Resampling frequency, i.e. the timeline is split into equal time chunks with ``freq`` value.
        :return: New instance of ``PoolData``
        """
        df = pd.DataFrame()
        pool = raw_data.pool
        df["c"] = raw_data.swaps["sqrt_price_x96"].transform(
            lambda x: Decimal(x)
            * Decimal(x)
            / Decimal(2 ** 192)
            * Decimal(10 ** pool.decimals_diff)
        )
        df["c_inv"] = 1 / df["c"]
        df["vol0"] = (
            (-raw_data.swaps["amount0"].where(raw_data.swaps["amount0"] < 0))
            .fillna(0)
            .transform(lambda x: Decimal(x) / 10 ** pool.token0.decimals)
        )
        df["vol1"] = (
            (-raw_data.swaps["amount1"].where(raw_data.swaps["amount1"] < 0))
            .fillna(0)
            .transform(lambda x: Decimal(x) / 10 ** pool.token1.decimals)
        )
        df["l"] = raw_data.swaps["liquidity"].transform(
            lambda x: Decimal(x) / 10 ** pool.l_decimals_diff
        )
        data = pd.DataFrame()
        mean = lambda x: np.nan if len(x) == 0 else Decimal(np.mean(x))
        sum = lambda x: np.sum(x)
        data["c"] = df["c"].resample(freq.value).agg(mean).ffill()
        data["c_inv"] = 1 / data["c"]
        data["vol0"] = df["vol0"].resample(freq.value).agg(sum)
        data["vol1"] = df["vol1"].resample(freq.value).agg(sum)
        data["l"] = df["l"].resample(freq.value).agg(mean)
        data["c"] = data["c"].transform(lambda x: float(x))
        data["c_inv"] = data["c_inv"].transform(lambda x: float(x))
        data["vol0"] = data["vol0"].transform(lambda x: float(x))
        data["vol1"] = data["vol1"].transform(lambda x: float(x))
        data["l"] = data["l"].transform(lambda x: float(x))
        data["vol"] = data["vol0"] * data["c"] + data["vol1"]
        data["fee"] = data["vol"] * pool.fee.percent

        return cls(data, raw_data.mints, raw_data.burns, pool, freq)

    @classmethod
    def from_pool(cls: PoolData, pool: Pool, freq: Frequency) -> PoolData:
        """
        Create ``PoolData`` for a specific pool

        :param pool: Pool specification
        :param freq: Resampling frequency, i.e. the timeline is split into equal time chunks with ``freq`` value.
        :return: New ``PoolData`` instance
        """
        raw = RawData.from_pool(pool)
        return cls.from_raw_data(raw, freq)

    @property
    def pool(self) -> Pool:
        """
        Pool specification
        """
        return self._pool

    @property
    def data(self) -> pd.DataFrame:
        """
        Transformed pandas data
        """
        return self._data

    def liquidity(self, t: datetime, c: float) -> float:
        """
        Get pool liquidity at time ``t`` and price ``c``

        :param t: Time for liquidity
        :param c: Current price for liquidity
        :return: Liquidity amount
        """
        res = 0
        tick = (np.log(c) - self._pool.decimals_diff * np.log(10)) / np.log(1.0001)
        for idx, mint in self._mints.iterrows():
            if idx > t:
                break
            if mint["tick_lower"] <= tick and mint["tick_upper"] >= tick:
                res += mint["amount"]
        for idx, burn in self._burns.iterrows():
            if idx > t:
                break
            if burn["tick_lower"] <= tick and burn["tick_upper"] >= tick:
                res -= burn["amount"]
        return res / 10 ** self._pool.l_decimals_diff

    def plot(self, sizex=20, sizey=30):
        """
        Plot pool data

        :param sizex: `x` size of one chart
        :param sizey: `y` size of one chart
        """
        fig, axes = plt.subplots(3, 2, figsize=(sizex, sizey))
        fig.suptitle(
            f"Stats for {self._pool.token0.value} - {self._pool.token1.value} pool",
            fontsize=16,
        )
        axes[0, 0].plot(self._data["c"], color=COLORS["c"])
        axes[0, 0].set_title(
            f"Price {self._pool.token1.value} / {self._pool.token0.value}"
        )
        axes[0, 0].tick_params(axis="x", labelrotation=45)
        axes[0, 1].plot(self._data["c_inv"], color=COLORS["c_inv"])
        axes[0, 1].set_title(
            f"Price {self._pool.token0.value} / {self._pool.token1.value}"
        )
        axes[0, 1].tick_params(axis="x", labelrotation=45)
        axes[1, 0].plot(self._data["vol"], color=COLORS["vol"])
        axes[1, 0].set_title(f"Trading volume")
        axes[1, 0].tick_params(axis="x", labelrotation=45)
        axes[1, 1].plot(self._data["fee"], color=COLORS["fee"])
        axes[1, 1].set_title(f"Fees")
        axes[1, 1].tick_params(axis="x", labelrotation=45)
        axes[2, 0].plot(self._data["l"], color=COLORS["l"])
        axes[2, 0].set_title(f"Liquidity dynamics")
        axes[2, 0].tick_params(axis="x", labelrotation=45)

        current_liquidity = LiquidityDistribution()
        current_liquidity.append(self._mints, self._burns)

        liq_start = int(
            np.log(float(self._data["c"].min() / 10 ** self._pool.decimals_diff / 2))
            / np.log(1.0001)
        )
        liq_end = int(
            np.log(float(self._data["c"].max() / 10 ** self._pool.decimals_diff * 2))
            / np.log(1.0001)
        )
        liq_x = np.linspace(liq_start, liq_end, 200)
        t = self._data.index[-1]
        axes[2, 1].plot(
            [1.0001 ** x * 10 ** self._pool.decimals_diff for x in liq_x],
            [current_liquidity.at(x) / 10 ** self._pool.l_decimals_diff for x in liq_x],
            color=COLORS["l"],
        )
        axes[2, 1].set_title(f"Liquidity at {t}")
        axes[2, 1].set_xlabel(
            f"{self._pool.token1.value} / {self._pool.token0.value} price"
        )

    def __getitem__(self, items) -> RawData:
        return PoolData(
            self._data.__getitem__(items),
            self._mints,
            self._burns,
            self._pool,
            self._freq,
        )


class LiquidityDistribution:
    def __init__(self):
        self._mints = IntervalTree()
        self._burns = IntervalTree()

    def append(self, mints: pd.DataFrame, burns: pd.DataFrame):
        self._mints.update(
            [
                Interval(mint["tick_lower"], mint["tick_upper"], int(mint["amount"]))
                for idx, mint in mints.iterrows()
            ]
        )
        self._burns.update(
            [
                Interval(burn["tick_lower"], burn["tick_upper"], int(burn["amount"]))
                for _idx, burn in burns.iterrows()
            ]
        )

    def at(self, tick: float):
        mint = 0
        [mint := mint + interval.data for interval in self._mints[tick]]
        burn = 0
        [burn := burn + interval.data for interval in self._burns[tick]]
        return mint - burn
