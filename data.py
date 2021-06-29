from enum import Enum
from io import StringIO
import boto3
import pandas as pd
import os


class Pool(Enum):
    ETHWBTC = "ETHWBTC"
    ETHUSDC = "ETHUSDC"


class Frequency(Enum):
    BLOCK = "15S"
    MINUTE = "min"
    MINUTE5 = "5min"
    MINUTE15 = "15min"
    HOUR = "H"
    DAY = "D"
    WEEK = "W"
    MONTH = "M"


class RawData:
    def __init__(self, pool: Pool, freq: Frequency):
        self._pool = pool
        self._freq = freq
        self.burns = self._fetch_pool_data("burns")
        self.mints = self._fetch_pool_data("mints")
        self.swaps = self._fetch_pool_data("swaps")

    def _fetch_pool_data(self, kind):
        aws_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

        client = boto3.client(
            "s3", aws_access_key_id=aws_id, aws_secret_access_key=aws_secret
        )

        bucket_name = os.getenv("AWS_DATA_BUCKET") or "mellow-uni-data"

        object_key = f"{kind}-{self._pool.value}.csv"
        csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)
        body = csv_obj["Body"]
        csv_string = body.read().decode("utf-8")

        return pd.read_csv(StringIO(csv_string))


data = RawData(Pool.ETHWBTC, Frequency.HOUR)
print(data.burns)
print(data.mints)
print(data.swaps)
