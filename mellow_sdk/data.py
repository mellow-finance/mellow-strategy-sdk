import os
from pathlib import Path
from decimal import Decimal
import subprocess
from datetime import datetime
import numpy as np
import polars as pl
import pandas as pd
from binance import Client
import boto3
from botocore.handlers import disable_signing
from botocore import UNSIGNED
from botocore.client import Config

from typing import List

from mellow_sdk.primitives import Pool
from mellow_sdk.utils import ConfigParser
from mellow_sdk.utils import log


class PoolDataUniV3:
    """
    ``PoolDataUniV3`` contains data for backtesting.

    Attributes:
        pool: UniswapV3 ``Pool`` data.
        mints: UniswapV3 mints data.
        burns: UniswapV3 burns data.
        swaps: UniswapV3 swaps data.
        full_df: All UniswapV3 events data.

    """
    def __init__(self,
                 pool: Pool,
                 mints: pl.DataFrame = None,
                 burns: pl.DataFrame = None,
                 swaps: pl.DataFrame = None,
                 full_df: pl.DataFrame = None,
                 ):

        self.pool = pool
        self.mints = mints
        self.burns = burns
        self.swaps = swaps
        self.full_df = full_df


class DownloadFromS3:
    """
    ``DownloadFromS3`` downloads data from S3 bucket.

    Attributes:
        data_dir: Directory where data will be downloaded.
        bucket_name: S3 bucket name.
    """
    def __init__(
            self,
            data_dir: str,
            bucket_name: str = 'mellow-public-data'
    )-> None:
        self.data_dir = data_dir
        self.bucket_name = bucket_name

    def check_dir(self) -> None:
        """
        Check if data directory exists. If not, create it.
        """
        path_dir = Path(self.data_dir)
        if not path_dir.is_dir():
            log.info('Created directory', directory=self.data_dir)
            path_dir.mkdir(parents=True, exist_ok=True)

    def get_last_files(self) -> List[str]:
        """
        Get last files from S3 bucket.

        Returns:
            List of latest files.
        """
        events = ['mint', 'burn', 'swap']
        s3 = boto3.resource('s3')
        s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
        bucket = s3.Bucket(self.bucket_name)
        suffixes = []
        for file in bucket.objects.all():
            name = file.key
            if 'mint' in name or 'burn' in name or 'swap' in name:
                date = '-'.join(name.split('.')[0].split('/')[-1].split('-')[1:])
                suffixes.append(date)
        last_date = sorted(suffixes)[-1]

        files = []
        for event in events:
            file = last_date[:-3] + '/' + 'history-' + last_date + '.' + event + '.csv'
            files.append(file)
        return files

    def get_file_from_s3(self, file: str) -> None:
        """
        Download file from S3 bucket and save it to directory.

        Args:
            file: File name.
        """
        s3client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

        file_name = '.'.join(file.split('.')[1:])
        path = self.data_dir + '/' + file_name
        s3client.download_file(self.bucket_name, file, path)

    def download_files(self) -> None:
        """
        Download all files from S3 bucket.
        """
        self.check_dir()
        files = self.get_last_files()
        for file in files:
            log.info(f'Download {file} from S3')
            self.get_file_from_s3(file)


class RawDataUniV3:
    """
        Load data from folder, preprocess and Return ``PoolDataUniV3`` instance.

        Attributes:
            pool: UniswapV3 ``Pool`` meta information.
            data_dir: Directory of data.
            reload_data: If True, reload data from S3.
    """
    def __init__(
            self,
            pool: Pool,
            data_dir: str,
            reload_data: bool = False
    )-> None:
        self.pool = pool
        self.data_dir = data_dir
        self.reload_data = reload_data

    def check_files(self) -> bool:
        """
        Check if all files are in the directory.

        Returns:
            True if all files are in the directory.
        """
        path_mint = Path(f'{self.data_dir}/mint.csv')
        path_burn = Path(f'{self.data_dir}/burn.csv')
        path_swap = Path(f'{self.data_dir}/swap.csv')
        res = path_mint.is_file() and path_burn.is_file() and path_swap.is_file()
        return res

    def load_mints(self) -> pl.DataFrame:
        """
            Read mints events from csv and preprocess.

        Returns:
            Preprocessed mints events data as dataframe.
        """
        mints_converters = {
            'pool': pl.Utf8,
            'block_hash': pl.Utf8,
            'tx_hash': pl.Utf8,
            'sender': pl.Utf8,
            'owner': pl.Utf8,
            "block_time": pl.Int64,
            "block_number": pl.Int64,
            'log_index': pl.Int64,
            "tick_lower": pl.Int64,
            "tick_upper": pl.Int64,
            "amount": pl.Float64,
            "amount0": pl.Float64,
            "amount1": pl.Float64,
        }
        file_name = f'{self.data_dir}/mint.csv'
        assert os.path.exists(file_name), f'File {file_name} does not exist.'

        df_mints_raw = pl.read_csv(file_name, dtypes=mints_converters)
        assert self.pool._address in df_mints_raw['pool'].unique(), f'Pool {self.pool._address} is not available yet.'
        df_mints = df_mints_raw.filter(pl.col('pool') == self.pool._address)

        df_prep = df_mints.select([
            pl.col('tx_hash'),
            pl.col('owner'),
            pl.col('block_number'),
            pl.col('log_index'),
            ((pl.col('block_time') * 1e3 + pl.col('log_index')) * 1e3).cast(pl.Datetime).alias('timestamp'),
            pl.col('tick_lower') + self.pool.tick_diff,
            pl.col('tick_upper') + self.pool.tick_diff,
            pl.col('amount0') / 10 ** self.pool.token0.decimals,
            pl.col('amount1') / 10 ** self.pool.token1.decimals,
            (pl.col('amount') / 10 ** self.pool.l_decimals_diff).alias('liquidity'),
        ]).with_column(
            pl.col('timestamp').dt.truncate("1d").alias('date')
        ).with_column(
            pl.Series(name='event', values=['mint'])
        ).sort(by=['block_number', 'log_index'])
        return df_prep

    def load_burns(self) -> pl.DataFrame:
        """
            Read burns events from csv and preprocess.

        Returns:
            Preprocessed burns events data as dataframe.
        """
        burns_converters = {
            'pool': pl.Utf8,
            'block_hash': pl.Utf8,
            'tx_hash': pl.Utf8,
            'owner': pl.Utf8,
            "block_time": pl.Int64,
            "block_number": pl.Int64,
            'log_index': pl.Int64,
            "tick_lower": pl.Int64,
            "tick_upper": pl.Int64,
            "amount": pl.Float64,
            "amount0": pl.Float64,
            "amount1": pl.Float64,
        }
        file_name = f'{self.data_dir}/burn.csv'
        assert os.path.exists(file_name), f'File {file_name} does not exist.'
        df_burns_raw = pl.read_csv(file_name, dtypes=burns_converters)
        assert self.pool._address in df_burns_raw['pool'].unique(), f'Pool {self.pool._address} is not available yet.'
        df_burns = df_burns_raw.filter(pl.col('pool') == self.pool._address)

        df_prep = df_burns.select([
            pl.col('tx_hash'),
            pl.col('owner'),
            pl.col('block_number'),
            pl.col('log_index'),
            ((pl.col('block_time') * 1e3 + pl.col('log_index')) * 1e3).cast(pl.Datetime).alias('timestamp'),
            pl.col('tick_lower') + self.pool.tick_diff,
            pl.col('tick_upper') + self.pool.tick_diff,
            pl.col('amount0') / 10 ** self.pool.token0.decimals,
            pl.col('amount1') / 10 ** self.pool.token1.decimals,
            (pl.col('amount') / 10 ** self.pool.l_decimals_diff).alias('liquidity'),
        ]).with_column(
            pl.col('timestamp').dt.truncate("1d").alias('date')
        ).filter(
            (pl.col('amount0') + pl.col('amount1')) > 1e-6
        ).with_column(
            pl.Series(name='event', values=['burn'])
        ).sort(by=['block_number', 'log_index'])
        return df_prep

    def load_swaps(self) -> pl.DataFrame:
        """
            Read burns events from csv and preprocess.

        Returns:
            Preprocessed swaps events data as dataframe.
        """
        swaps_converters = {
            'pool': pl.Utf8,
            'block_hash': pl.Utf8,
            'tx_hash': pl.Utf8,
            'sender': pl.Utf8,
            'recipient': pl.Utf8,
            "block_time": pl.Int64,
            "block_number": pl.Int64,
            'log_index': pl.Int64,
            "tick": pl.Int64,
            "liquidity": pl.Float64,
            "amount0": pl.Float64,
            "amount1": pl.Float64,
            'sqrt_price_x96': pl.Float64,
        }
        file_name = f'{self.data_dir}/swap.csv'
        assert os.path.exists(file_name), f'File {file_name} does not exist.'

        df_swaps_raw = pl.read_csv(file_name, dtypes=swaps_converters)
        assert self.pool._address in df_swaps_raw['pool'].unique(), f'Pool {self.pool._address} is not available yet.'
        df_swaps = df_swaps_raw.filter(pl.col('pool') == self.pool._address)

        df_prep = df_swaps.select([
            pl.col('tx_hash'),
            pl.col('sender').alias('owner'),
            pl.col('block_number'),
            pl.col('log_index'),
            ((pl.col('block_time') * 1e3 + pl.col('log_index')) * 1e3).cast(pl.Datetime).alias('timestamp'),
            pl.col('amount0') / 10 ** self.pool.token0.decimals,
            pl.col('amount1') / 10 ** self.pool.token1.decimals,
            (pl.col('liquidity') / 10 ** self.pool.l_decimals_diff).alias('liquidity'),
            pl.col('tick') + self.pool.tick_diff,
            pl.col('sqrt_price_x96'),
        ]).sort(by=['block_number', 'log_index']).with_column(
            pl.col("sqrt_price_x96").apply(
                lambda x: float((Decimal(x) * Decimal(x)) / (Decimal(2 ** 192) / Decimal(10 ** self.pool.decimals_diff)))).alias('price')
        ).with_columns([
            pl.col('price').shift_and_fill(1, pl.col('price').first()).alias('price_before'),
            pl.col('price').shift_and_fill(-1, pl.col('price').last()).alias('price_next'),
            pl.col('timestamp').dt.truncate("1d").alias('date'),
            pl.Series(name='event', values=['swap'])
        ]).drop("sqrt_price_x96").sort(by=['block_number', 'log_index'])
        return df_prep

    def load_from_folder(self) -> PoolDataUniV3:
        """
            Check if directory exists and load data from it. If not, create it.
            Load mints, burns, swaps events from folder and preprocess them.
            Create all UniV3 events dataframe.
            Create ``PoolDataUniV3`` object.

        Returns:
            `PoolDataUniV3`` object.
        """
        if self.reload_data or (not self.check_files()):
            downloader = DownloadFromS3(self.data_dir)
            downloader.download_files()

        mints = self.load_mints()
        burns = self.load_burns()
        swaps = self.load_swaps()

        full_df = (
                pl.concat([swaps, mints, burns], how='diagonal')
                .sort(by=['block_number', 'log_index'])
                .with_columns(
                [
                    pl.col('price').forward_fill().backward_fill(),
                    pl.col('tick').forward_fill().backward_fill()
                ]
            )
        )
        return PoolDataUniV3(self.pool, mints, burns, swaps, full_df)


class SyntheticData:
    """
    | ``SyntheticData`` generates UniswapV3 synthetic exchange data (swaps df).
    | Generates by sampling Geometric Brownian Motion.

    Attributes:
        pool:
            UniswapV3 ``Pool`` meta information.
        start_date:
            Generating starting date. (example '1-1-2022')
        end_date:
            Generating ending date. (example '31-12-2022')
        frequency:
            Generating frequency. (example '1d')
        init_price:
            Initial price.
        mu:
            Expectation of normal distribution.
        sigma:
            Variance of normal distribution.
        seed:
            Seed for random generator.
   """
    def __init__(
            self,
            pool: Pool,
            start_date: datetime = datetime(2022, 1, 1),
            end_date: datetime = datetime(2022, 12, 31),
            frequency: str = '1d',
            init_price: float = 1.,
            mu: float = 0,
            sigma: float = 0.1,
            seed: int = 42
    )-> None:

        self.pool = pool
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency

        self.init_price = init_price
        self.mu = mu
        self.sigma = sigma

        self.seed = seed

    def generate_data(self) -> PoolDataUniV3:
        """
        Generate synthetic UniswapV3 exchange data.

        Returns:
            ``PoolDataUniV3`` instance with synthetic swaps data.
        """
        timestamps = pl.date_range(self.start_date, self.end_date, self.frequency).to_list()

        price_log_returns = np.random.normal(loc=self.mu, scale=self.sigma, size=len(timestamps))
        price_returns = np.exp(price_log_returns)
        price_returns[0] = self.init_price
        prices = np.cumprod(price_returns)

        timestamps = pl.Series(name='timestamp', values=timestamps)
        prices = pl.Series(name='price', values=prices, dtype=pl.Float64)

        df = pl.DataFrame([timestamps, prices]).with_column(pl.col('timestamp').cast(pl.Datetime))

        df = df.with_columns([
            pl.col('price').shift_and_fill(1, pl.col('price').first()).alias('price_before'),
            pl.col('price').shift_and_fill(-1, pl.col('price').last()).alias('price_after'),
        ])
        df = df.with_column((np.trunc(np.log(pl.col('price')) / np.log(1.0001))).alias('tick'))

        return PoolDataUniV3(self.pool, swaps=df)


class DownloaderBinanceData:
    """
        Download pair data from binance and write csv to data folder.

    Attributes:
        pair_name: 'ethusdc' or other
        interval: Binance interval string, e.g.:
            '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w'
        start_date: String in format '%d-%M-%Y' (utc time format), (example '05-12-2018')
        end_date: String in format '%d-%M-%Y' (utc time format)
        config_path: path to yml config with config['binance']['api_key'], config['binance']['api_secret']
        data_dir: path to data folder
    """

    def __init__(
        self,
        pair_name: str,
        interval: str,
        start_date: str,
        end_date: str,
        config_path: str,
        data_dir: str
    ) -> None:

        self.pair_name = str.upper(pair_name)
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.config_path = config_path
        self.data_dir = data_dir

        subprocess.run(['mkdir', '-p', self.data_dir])

    def get(self) -> pd.DataFrame:
        """
        Get market data from Binance.

        Returns:
            pandas dataframe that was written to the /data/f'{pair_name}_{interval}_{start_str}_{end_str}.csv'
        """
        # in - ms
        # in * 1000 - us
        # we need to get the num of sec in the interval
        map_dict = {'m': 1, 'h': 60, 'd': 24 * 60, 'w': 7 * 24 * 60}
        # num of nano sec [us]
        us_num = int(self.interval[0:-1]) * map_dict[self.interval[-1]] * 60 * 1000 * 1000

        # binance api client
        config = ConfigParser(config_path=self.config_path).config
        client = Client(
            config['binance']['api_key'],
            config['binance']['api_secret']
        )

        # download candles
        print('start:', datetime.now())
        try:
            klines = client.get_historical_klines(
                symbol=self.pair_name,
                interval=self.interval,
                start_str=self.start_date,
                end_str=self.end_date
            )
        except:
            assert False, 'using the api failed'
        print('finish:', datetime.now())
        print('rows downloaded:', len(klines))
        assert len(klines) > 1, '0 or 1 rows downloaded!'

        # preparing to timestamp to nano sec datetime[us]
        ts = [i[0] * 1000 for i in klines]
        index_col = list(range(ts[0], ts[-1] + us_num, us_num))

        # convert price to float
        price_col = [float(i[4]) for i in klines]

        # create dataframe
        df = pd.DataFrame({'price': [np.nan]}, index=index_col)
        df.index.name = 'timestamp'

        mismatch_rows = list(set(ts) - set(index_col))
        print('mismatch timestamp rows: ', len(mismatch_rows))

        data = np.array([ts, price_col])
        data = data[:, np.isin(data[0, :], mismatch_rows, invert=True)]

        df.loc[data[0, :], 'price'] = data[1, :]
        df.index = pd.to_datetime(df.index, unit='us')

        df['price'] = df['price'].shift(1)
        df = df.iloc[1:]
        df = df.reset_index()

        file_name = f'{self.pair_name}_{self.interval}_{self.start_date}_{self.end_date}.csv'
        file_path = os.path.join(self.data_dir, file_name)

        df.to_csv(file_path, index=False, date_format='%Y-%m-%d %H:%M:%S:%f')
        print(f'df shape {df.shape} saved to {file_path}')
        return df
