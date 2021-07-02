import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from strategy.primitives import Pool, Token, Frequency
from decimal import Decimal
from datetime import datetime
from intervaltree import IntervalTree, Interval


class RawData:
    def __init__(self, pool: Pool):
        self._pool = pool
        print(f"Downloading swaps")
        self.swaps = pd.read_csv(
            self._get_download_url("swaps"),
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
        self.swaps.index = pd.to_datetime(self.swaps["block_time"], unit="s")
        print(f"Downloading burns")
        self.burns = pd.read_csv(
            self._get_download_url("burns"),
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
        self.burns.index = pd.to_datetime(self.burns["block_time"], unit="s")
        print(f"Downloading mints")
        self.mints = pd.read_csv(
            self._get_download_url("mints"),
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
        self.mints.index = pd.to_datetime(self.mints["block_time"], unit="s")
        print("Done")

    def pool(self) -> Pool:
        return self._pool

    def _get_download_url(self, kind):
        host = (
            os.getenv("AWS_DATA_HOST") or "mellow-uni-data.s3.us-east-2.amazonaws.com"
        )
        return f"https://{host}/{kind}-{self._pool.name()}.csv"


class PoolData:
    def __init__(self, raw_data: RawData, freq: Frequency):
        self._pool = raw_data.pool()
        self._freq = freq
        self._mints = raw_data.mints
        self._burns = raw_data.burns
        df = pd.DataFrame()
        decimals_diff = self._pool.token0().decimals() - self._pool.token1().decimals()
        liquidity_decimals_diff = int(
            (self._pool.token0().decimals() + self._pool.token1().decimals()) / 2
        )
        df["c"] = raw_data.swaps["sqrt_price_x96"].transform(
            lambda x: Decimal(x)
            * Decimal(x)
            / Decimal(2 ** 192)
            * Decimal(10 ** decimals_diff)
        )
        df["c_inv"] = 1 / df["c"]
        df["vol0"] = (
            (-raw_data.swaps["amount0"].where(raw_data.swaps["amount0"] < 0))
            .fillna(0)
            .transform(lambda x: Decimal(x) / 10 ** self._pool.token0().decimals())
        )
        df["vol1"] = (
            (-raw_data.swaps["amount1"].where(raw_data.swaps["amount1"] < 0))
            .fillna(0)
            .transform(lambda x: Decimal(x) / 10 ** self._pool.token1().decimals())
        )
        df["l"] = raw_data.swaps["liquidity"].transform(
            lambda x: Decimal(x) / 10 ** liquidity_decimals_diff
        )
        self._data = pd.DataFrame()
        mean = lambda x: np.nan if len(x) == 0 else Decimal(np.mean(x))
        sum = lambda x: np.sum(x)
        self._data["c"] = df["c"].resample(freq.value).agg(mean).ffill()
        self._data["c_inv"] = 1 / self._data["c"]
        self._data["vol0"] = df["vol0"].resample(freq.value).agg(sum)
        self._data["vol1"] = df["vol1"].resample(freq.value).agg(sum)
        self._data["l"] = df["l"].resample(freq.value).agg(mean)
        self._data["c"] = self._data["c"].transform(lambda x: float(x))
        self._data["c_inv"] = self._data["c_inv"].transform(lambda x: float(x))
        self._data["vol0"] = self._data["vol0"].transform(lambda x: float(x))
        self._data["vol1"] = self._data["vol1"].transform(lambda x: float(x))
        self._data["l"] = self._data["l"].transform(lambda x: float(x))

    def pool(self) -> Pool:
        return self._pool

    def data(self) -> pd.DataFrame:
        return self._data

    def liquidity(self, t: datetime, c: float):
        res = 0
        for idx, mint in self._mints.iterrows():
            # if idx > t:
            #     break
            if mint["tick_lower"] <= c and mint["tick_upper"] >= c:
                res += mint["amount"]
        for idx, burn in self._burns.iterrows():
            # if idx > t:
            #     break
            if burn["tick_lower"] <= c and burn["tick_upper"] >= c:
                res -= burn["amount"]
        liquidity_decimals_diff = int(
            (self._pool.token0().decimals() + self._pool.token1().decimals()) / 2
        )
        return res / 10 ** liquidity_decimals_diff

    def plot(self, sizex=20, sizey=30):
        """
        Plot tracking data

        :param sizex: `x` size of one chart
        :param sizey: `y` size of one chart
        """
        fig, axes = plt.subplots(3, 2, figsize=(sizex, sizey))
        fig.suptitle(
            f"Stats for {self._pool.token0().value} - {self._pool.token1().value} pool",
            fontsize=16,
        )
        axes[0, 0].plot(self._data["c"], color="#bb6600")
        axes[0, 0].set_title(
            f"Price {self._pool.token1().value} / {self._pool.token0().value}"
        )
        axes[0, 0].tick_params(axis="x", labelrotation=45)
        axes[0, 1].plot(self._data["c_inv"], color="#00bbbb")
        axes[0, 1].set_title(
            f"Price {self._pool.token0().value} / {self._pool.token1().value}"
        )
        axes[0, 1].tick_params(axis="x", labelrotation=45)
        axes[1, 0].plot(self._data["vol0"], color="#bb6600")
        axes[1, 0].set_title(f"Trading volume {self._pool.token0().value}")
        axes[1, 0].tick_params(axis="x", labelrotation=45)
        axes[1, 1].plot(self._data["vol1"], color="#00bbbb")
        axes[1, 1].set_title(f"Trading volume {self._pool.token1().value}")
        axes[1, 1].tick_params(axis="x", labelrotation=45)
        axes[2, 0].plot(self._data["l"], color="#0000bb")
        axes[2, 0].set_title(f"Liquidity dynamics")
        axes[2, 0].tick_params(axis="x", labelrotation=45)

        current_liquidity = LiquidityDistribution()
        current_liquidity.append(self._mints, self._burns)

        decimals_diff = self._pool.token0().decimals() - self._pool.token1().decimals()
        liquidity_decimals_diff = int(
            (self._pool.token0().decimals() + self._pool.token1().decimals()) / 2
        )

        liq_start = int(
            np.log(float(self._data["c"].min() / 10 ** decimals_diff / 2))
            / np.log(1.0001)
        )
        liq_end = int(
            np.log(float(self._data["c"].max() / 10 ** decimals_diff * 2))
            / np.log(1.0001)
        )
        liq_x = np.linspace(liq_start, liq_end, 200)
        t = self._data.index[-1]
        axes[2, 1].plot(
            [1.0001 ** x * 10 ** decimals_diff for x in liq_x],
            [current_liquidity.at(x) / 10 ** liquidity_decimals_diff for x in liq_x],
            color="#0000bb",
        )
        axes[2, 1].set_title(f"Liquidity at {t}")
        axes[2, 1].set_xlabel(
            f"{self._pool.token1().value} / {self._pool.token0().value} price"
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
                for idx, burn in burns.iterrows()
            ]
        )

    def at(self, tick: float):
        mint = 0
        [mint := mint + interval.data for interval in self._mints[tick]]
        burn = 0
        [burn := burn + interval.data for interval in self._burns[tick]]
        return mint - burn
