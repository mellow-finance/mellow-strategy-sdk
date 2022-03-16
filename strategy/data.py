import os
from pathlib import Path
from decimal import Decimal
import subprocess
import numpy as np
import pandas as pd
import polars as pl
from datetime import datetime
from strategy.primitives import Pool, POOLS
from utilities.utilities import get_db_connector, get_main_path


class PoolDataUniV3:
    """
    ``PoolDataUniV3`` contains data for backtesting.

    Attributes:
        pool: UniswapV3 ``Pool`` data
        mints: UniswapV3 mints data.
        burns: UniswapV3 burns data.
        swaps: UniswapV3 swaps data.
    """
    def __init__(self,
                 pool: Pool,
                 mints: pd.DataFrame = None,
                 burns: pd.DataFrame = None,
                 swaps: pd.DataFrame = None
                 ):

        self.pool = pool
        self.mints = mints
        self.burns = burns
        self.swaps = swaps


class RawDataUniV3:
    """
        Load data from folder, preprocess and Return ``PoolDataUniV3`` instance.
    """
    def __init__(self, pool: Pool, data_dir: Path = None):
        self.pool = pool

        if not data_dir:
            root = get_main_path()
            self.data_dir = os.path.join(root, 'data')
        else:
            self.data_dir = data_dir

    def load_mints(self) -> pl.DataFrame:
        """
            read mints from csv and preprocess
        Returns:
            mints df
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
        df_mints = pl.read_csv(f'{self.data_dir}/mint_{self.pool.name}.csv', dtypes=mints_converters)
        df_prep = df_mints.select([
            pl.col('tx_hash'),
            pl.col('owner'),
            pl.col('block_number'),
            pl.col('log_index'),
            ((pl.col('block_time') * 1e3 + pl.col('log_index')) * 1e3).cast(pl.Datetime).alias('timestamp'),
            pl.col('tick_lower'),
            pl.col('tick_upper'),
            pl.col('amount0') / 10 ** self.pool.token0.decimals,
            pl.col('amount1') / 10 ** self.pool.token1.decimals,
            (pl.col('amount') * 10 ** self.pool.decimals_diff).alias('liquidity'),
        ]).with_column(
            pl.col('timestamp').dt.truncate("1d").alias('date')
        ).sort(by=['block_number', 'log_index'])
        return df_prep

    def load_burns(self) -> pl.DataFrame:
        """
            read burns from csv and preprocess
        Returns:
            burns df
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
        df_burns = pl.read_csv(f'{self.data_dir}/burn_{self.pool.name}.csv', dtypes=burns_converters)
        df_prep = df_burns.select([
            pl.col('tx_hash'),
            pl.col('owner'),
            pl.col('block_number'),
            pl.col('log_index'),
            ((pl.col('block_time') * 1e3 + pl.col('log_index')) * 1e3).cast(pl.Datetime).alias('timestamp'),
            pl.col('tick_lower'),
            pl.col('tick_upper'),
            pl.col('amount0') / 10 ** self.pool.token0.decimals,
            pl.col('amount1') / 10 ** self.pool.token1.decimals,
            (pl.col('amount') * 10 ** self.pool.decimals_diff).alias('liquidity'),
        ]).with_column(
            pl.col('timestamp').dt.truncate("1d").alias('date')
        ).filter(
            (pl.col('amount0') + pl.col('amount1')) > 1e-6
        ).sort(by=['block_number', 'log_index'])
        return df_prep

    def load_swaps(self) -> pl.DataFrame:
        """
            read swaps from csv, preprocess, create sqrt_price_x96 column.
        Returns:
            swaps df
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
        df_swaps = pl.read_csv(f'{self.data_dir}/swap_{self.pool.name}.csv', dtypes=swaps_converters)
        df_prep = df_swaps.select([
            pl.col('tx_hash'),
            pl.col('sender'),
            pl.col('recipient'),
            pl.col('block_number'),
            pl.col('log_index'),
            ((pl.col('block_time') * 1e3 + pl.col('log_index')) * 1e3).cast(pl.Datetime).alias('timestamp'),
            pl.col('amount0') / 10 ** self.pool.token0.decimals,
            pl.col('amount1') / 10 ** self.pool.token1.decimals,
            (pl.col('liquidity') * 10 ** self.pool.decimals_diff),
            pl.col('tick'),
            pl.col('sqrt_price_x96')
        ]).with_column(
            pl.col('timestamp').dt.truncate("1d").alias('date')
        ).with_column(
            pl.col("sqrt_price_x96").apply(
                lambda x: float((Decimal(x) * Decimal(x)) / (Decimal(2 ** 192) / Decimal(10 ** self.pool.decimals_diff)))).alias('price')
        ).with_columns([
            pl.col('price').shift_and_fill(1, pl.col('price').first()).alias('price_before'),
            pl.col('price').shift_and_fill(-1, pl.col('price').last()).alias('price_next')
        ]).sort(by=['block_number', 'log_index'])

        return df_prep

    def load_from_folder(self) -> PoolDataUniV3:
        """
            Load mints, burns, swaps from folder, preprocess and create ``PoolDataUniV3`` object.
        Returns:
            `PoolDataUniV3`` object
        """
        mints = self.load_mints()
        burns = self.load_burns()
        swaps = self.load_swaps()
        return PoolDataUniV3(self.pool, mints, burns, swaps)


class SyntheticData:
    """
    | ``SyntheticData`` generates UniswapV3 synthetic exchange data (swaps df).
    | Generates by sampling Geometric Brownian Motion.
    Attributes:
        pool:
            UniswapV3 ``Pool`` instance.
        start_date:
            Generating starting date. (example '1-1-2022')
        n_points:
            Amount samples to generate.
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
            self, pool, start_date: str = '1-1-2022', n_points: int = 365,
            init_price: float = 1, mu: float = 0, sigma: float = 0.1, seed=42):
        self.pool = pool
        self.start_date = start_date
        self.n_points = n_points

        self.init_price = init_price
        self.mu = mu
        self.sigma = sigma

        self.seed = seed

    def generate_data(self):
        """
        Generate synthetic UniswapV3 exchange data.

        Returns:
            ``PoolDataUniV3`` instance with synthetic swaps data, mint is None, burn is None.
        """
        timestamps = pd.date_range(start=self.start_date, periods=self.n_points, freq='D', normalize=True)
        # np.random.seed(self.seed)
        price_log_returns = np.random.normal(loc=self.mu, scale=self.sigma, size=self.n_points)
        price_returns = np.exp(price_log_returns)
        price_returns[0] = self.init_price

        prices = np.cumprod(price_returns)

        df = pd.DataFrame(zip(timestamps, prices), columns=['timestamp', 'price']).set_index('timestamp')

        df["price_before"] = df["price"].shift(1)
        df["price_before"] = df["price_before"].bfill()

        df["price_next"] = df["price"].shift(-1)
        df["price_next"] = df["price_next"].ffill()

        df = pl.from_pandas(df.reset_index())

        return PoolDataUniV3(self.pool, mints=None, burns=None, swaps=df)


class DownloaderRawDataUniV3:
    # TODO docs
    # TODO S3
    """
        downloader of raw data from db
    """
    def __init__(self):
        self.db_connection = get_db_connector()
        self.root = get_main_path()
        subprocess.run(['mkdir', '-p', os.path.join(self.root, 'data')])

    def _get_event(self, event: str, pool_address: str, file_name: Path):
        """
            private func, download event from pool and save it
        Args:
            event: 'mint', 'burn' or 'swap'
            pool_address:
            file_name: file name to save in mellow-strategy-sdk/data/
        Returns:
            None
        """
        print(f'get {event}')
        query = f'select * from {event} WHERE pool="{pool_address}" ORDER BY block_time'

        try:
            if event == 'burn':
                query = f"""
                    select
                        pool,
                        block_number,
                        block_hash,
                        block_time,
                        log_index,
                        tx_hash,
                        owner,
                        (tick_lower div 1) as tick_lower,
                        (tick_upper div 1) as tick_upper,
                        cast(amount as char) as amount,
                        cast(amount0 as char) as amount0,
                        cast(amount1 as char) as amount1
                    from {event} 
                    WHERE pool="{pool_address}" 
                    ORDER BY block_time
                """
                df = pd.read_sql_query(query, con=self.db_connection)
            if event == 'mint':
                query = f"""
                    select
                        pool,
                        block_number,
                        block_hash,
                        block_time,
                        log_index,
                        tx_hash,
                        sender,
                        owner,
                        (tick_lower div 1) as tick_lower,
                        (tick_upper div 1) as tick_upper,
                        cast(amount as char) as amount,
                        cast(amount0 as char) as amount0,
                        cast(amount1 as char) as amount1
                    from {event} 
                    WHERE pool="{pool_address}" 
                    ORDER BY block_time
                """
                df = pd.read_sql_query(query, con=self.db_connection)

            if event == 'swap':
                query = f"""
                    select
                        pool,
                        block_number,
                        block_hash,
                        block_time,
                        log_index,
                        tx_hash,
                        sender,
                        recipient,
                        cast(amount0 as char) as amount0,
                        cast(amount1 as char) as amount1,
                        cast(sqrt_price_x96 as char) as sqrt_price_x96,
                        cast(liquidity as char) as liquidity,
                        (tick div 1) as tick

                    from {event} 
                    WHERE pool="{pool_address}" 
                    ORDER BY block_time
                """
                df = pd.read_sql_query(query, con=self.db_connection)

            df.to_csv(f'{self.root}/data/{file_name}', index=False)
            print(f'saved to {file_name}')
        except Exception as e:
            print(e)
            print(f'Failed to download from db or save to {file_name}')

    def load_events(self, pool_number: int):
        """
        by pool_number download all events in separate files
        Args:
            pool_number:
        Returns:
            None
        """
        pool_address = POOLS[pool_number]['address']
        file_name_base = POOLS[pool_number]['token0'].name + '_' + POOLS[pool_number]['token1'].name + '_' + str(
            POOLS[pool_number]['fee'].value) + '.csv'

        events = ["burn", "mint", "swap"]

        for event in events:
            file_name = event + '_' + file_name_base
            self._get_event(event, pool_address, file_name)

    def get_transactions(self):
        """
            download all transactions
        Returns:

        """
        file_name = "all_transactions.csv"

        query = f"""
        select 
            hash, block_number, gas, gas_price
            from transaction
            ORDER BY block_time
        """
        try:
            df = pd.pandas.read_sql_query(query, con=self.db_connection, dtype={
                'hash': str,
                'block_number': int,
                'gas': int,
                'gas_price': int
            })

            df.to_csv(f'{self.root}/data/{file_name}', index=False)
            print(f'saved to {file_name}')
        except:
            print(f'Failed to download from db or save to {file_name}')


    # def get_curvefi(self):
    #     """
    #         Doesnt work, Doesnt need for while
    #     Args:
    #         self:
    #
    #     Returns:
    #
    #     """
    #     event = 'curve_steth_eth'
    #     file_name = "curve_steth_eth.csv"
    #
    #     print(f'get {event}')
    #     query = f'select * from {event}'
    #     try:
    #         df = pd.read_sql(query, con=self.db_connection)
    #         df.to_csv(f'{self.root}/data/{file_name}', index=False)
    #         print(f'saved to {file_name}')
    #     except:
    #         print(f'Failed to download from db or save to {file_name}')

