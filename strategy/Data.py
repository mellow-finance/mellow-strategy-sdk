import numpy as np
import pandas as pd
from pathlib import Path
from decimal import Decimal

from strategy.primitives import Pool
from strategy.primitives import POOLS
from utilities import get_db_connector, get_main_path

import os
import sys


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
      ``RawDataUniV3`` preprocess UniswapV3 data.
      Attributes:
         pool: UniswapV3 pool meta data.
         folder: path to data.
   """
    def __init__(self, pool: Pool, folder: Path = '../data/'):
        self.pool = pool
        self.folder = folder

    def load_from_folder(self) -> PoolDataUniV3:
        """
        Loads data: swaps, mint, burns from predefined folder.
        Returns:
            PoolDataUniV3 instance with loaded data.
        """

        mints_converters = {
            "block_time": int,
            "block_number": int,
            "tick_lower": int,
            "tick_upper": int,
            "amount": int,
            "amount0": int,
            "amount1": int,
        }
        df_mint = pd.read_csv(f'{self.folder}mint_{self.pool.name}.csv', converters=mints_converters)

        burns_converts = {
            "block_time": int,
            "block_number": int,
            "tick_lower": int,
            "tick_upper": int,
            "amount": int,
            "amount0": int,
            "amount1": int,
        }
        df_burn = pd.read_csv(f'{self.folder}burn_{self.pool.name}.csv', converters=burns_converts)

        swap_converters = {
            "block_time": int,
            "block_number": int,
            "sqrt_price_x96": int,
            "amount0": int,
            "amount1": int,
            "liquidity": int,
        }
        df_swap = pd.read_csv(f'{self.folder}swap_{self.pool.name}.csv', converters=swap_converters)

        mints = self.preprocess_mints(df_mint)
        burns = self.preprocess_burns(df_burn)
        swaps = self.preprocess_swaps(df_swap)
        return PoolDataUniV3(self.pool, mints, burns, swaps)

    def preprocess_mints(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess UniswapV3 mints data.
        Args:
            df: Mints data frame.
        Returns:
            Preprocessed mints data frame.
        """
        df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
        df = df.set_index('timestamp')
        df = df.sort_values(by=['timestamp', 'amount'], ascending=[True, False]) # TODO: amount -> log_index ??
        df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
        df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
        df['amount'] = df['amount'] / 10**(-self.pool.decimals_diff)
        return df

    def preprocess_burns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess UniswapV3 burns data.
        Args:
            df: Burns data frame.
        Returns:
            Preprocessed burns data frame.
        """
        df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
        df = df.set_index('timestamp')
        df = df.sort_values(by=['timestamp', 'amount'], ascending=[True, False])
        df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
        df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
        df['amount'] = df['amount'] / 10**(-self.pool.decimals_diff)
        return df

    def preprocess_swaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess UniswapV3 swap data.
        Args:
            df: Swaps data frame.
        Returns:
            Preprocessed swap data frame.
        """

        df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
        df['timestamp'] = df['timestamp'] + pd.to_timedelta(df['log_index'], unit='ns')
        df = df.sort_values(by='timestamp', ascending=True)
        df = df.set_index('timestamp')
        df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
        df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
        df['liquidity'] = df['liquidity'] / 10**(-self.pool.decimals_diff)

        df["price"] = df["sqrt_price_x96"].transform(
                lambda x: float(Decimal(x) * Decimal(x) / (Decimal(2 ** 192) * Decimal(10 ** (-self.pool.decimals_diff))))
                        )
        df["price_before"] = df["price"].shift(1)
        df["price_before"] = df["price_before"].bfill()

        df["price_next"] = df["price"].shift(-1)
        df["price_next"] = df["price_next"].ffill()

        return df


class SyntheticData:
    """
       ``SyntheticData`` generates UniswapV3 synthetic exchange data.
       Attributes:
            pool: UniswapV3 ``Pool`` instance.
            start_date: Generating starting date.
            n_points: Amount samples to generate.
            init_price: Initial price.
            mu: Expectation of normal distribution.
            sigma: Variance of normal distributio.
            seed: Seed for random generator.
   """
    def __init__(self, pool, start_date='1-1-2022', n_points=365, init_price=1, mu=0, sigma=0.1, seed=42):
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
            PoolDataUniV3 instance with synthetic data.
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
        
        return PoolDataUniV3(self.pool, mints=None, burns=None, swaps=df)


class DownloaderRawDataUniV3:
    """
        downloader of raw data from db
    """
    def __init__(self):
        self.db_connection = get_db_connector()
        self.root = get_main_path()


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
                print()
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



# for future
# class RawDataUniV3New:
#     """
#       ``RawDataUniV3`` preprocess UniswapV3 data.
#       Attributes:
#          pool: UniswapV3 pool meta data.
#          folder: path to data.
#    """
#     def __init__(self, pool: Pool, folder: Path = '../data/'):
#         self.pool = pool
#         self.folder = folder
#
#     def load_from_folder(self) -> PoolDataUniV3:
#         """
#         Loads data: swaps, mint, burns from predefined folder.
#         Returns:
#             PoolDataUniV3 instance with loaded data.
#         """
#
#         mints_converters = {
#             "block_time": int,
#             "block_number": int,
#             "tick_lower": int,
#             "tick_upper": int,
#             "amount": int,
#             "amount0": int,
#             "amount1": int,
#         }
#         df_mint = pd.read_csv(f'{self.folder}mint_{self.pool.name}.csv', converters=mints_converters)
#
#         burns_converts = {
#             "block_time": int,
#             "block_number": int,
#             "tick_lower": int,
#             "tick_upper": int,
#             "amount": int,
#             "amount0": int,
#             "amount1": int,
#         }
#         df_burn = pd.read_csv(f'{self.folder}burn_{self.pool.name}.csv', converters=burns_converts)
#
#         swap_converters = {
#             "block_time": int,
#             "block_number": int,
#             "sqrt_price_x96": int,
#             "amount0": int,
#             "amount1": int,
#             "liquidity": int,
#         }
#         df_swap = pd.read_csv(f'{self.folder}swap_{self.pool.name}.csv', converters=swap_converters)
#
#         mints = self.preprocess_mints(df_mint)
#         burns = self.preprocess_burns(df_burn)
#         swaps = self.preprocess_swaps(df_swap)
#         return PoolDataUniV3(self.pool, mints, burns, swaps)
#
#     def preprocess_mints(self, df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Preprocess UniswapV3 mints data.
#         Args:
#             df: Mints data frame.
#         Returns:
#             Preprocessed mints data frame.
#         """
#         df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
#         df = df.set_index('timestamp')
#         df = df.sort_values(by=['block_number', 'log_index'])
#         df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
#         df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
#         df['amount'] = df['amount'] / 10**(-self.pool.decimals_diff)
#
#         df = df.set_index(['block_number', 'log_index'])
#         return df
#
#     def preprocess_burns(self, df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Preprocess UniswapV3 burns data.
#         Args:
#             df: Burns data frame.
#         Returns:
#             Preprocessed burns data frame.
#         """
#         df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
#         df = df.set_index('timestamp')
#         df = df.sort_values(by=['block_number', 'log_index'])
#         df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
#         df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
#         df['amount'] = df['amount'] / 10**(-self.pool.decimals_diff)
#         return df
#
#     def preprocess_swaps(self, df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Preprocess UniswapV3 swap data.
#         Args:
#             df: Swaps data frame.
#         Returns:
#             Preprocessed swap data frame.
#         """
#
#         df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
#         df['timestamp'] = df['timestamp'] + pd.to_timedelta(df['log_index'], unit='ns')
#         df = df.sort_values(by=['block_number', 'log_index'])
#         df = df.set_index('timestamp')
#         df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
#         df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
#         df['liquidity'] = df['liquidity'] / 10**(-self.pool.decimals_diff)
#
#         df["price"] = df["sqrt_price_x96"].transform(
#                 lambda x: float(Decimal(x) * Decimal(x) / (Decimal(2 ** 192) * Decimal(10 ** (-self.pool.decimals_diff))))
#                         )
#         df["price_before"] = df["price"].shift(1)
#         df["price_before"] = df["price_before"].bfill()
#
#         df["price_next"] = df["price"].shift(-1)
#         df["price_next"] = df["price_next"].ffill()
#
#         return df