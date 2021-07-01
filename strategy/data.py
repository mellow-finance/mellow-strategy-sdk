import pandas as pd
import os
from strategy.primitives import Pool


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

    def _get_download_url(self, kind):
        host = (
            os.getenv("AWS_DATA_HOST") or "mellow-uni-data.s3.us-east-2.amazonaws.com"
        )
        return f"https://{host}/{kind}-{self._pool.name()}.csv"
