import numpy as np
import pandas as pd
from pathlib import Path
from decimal import Decimal

from strategy.primitives import Pool


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
        folder: Path to data.
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
        df = df.sort_values(by=['timestamp', 'amount'], ascending=[True, False])
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
