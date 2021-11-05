import pandas as pd
from pathlib import Path
from decimal import Decimal
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .primitives import Pool


class PoolDataUniV3:
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

    @classmethod
    def from_folder(cls, pool: Pool, folder: Path = '../scripts/data/') -> 'PoolDataUniV3':
        mints_converters = {
            "block_time": int,
            "block_number": int,
            "tick_lower": int,
            "tick_upper": int,
            "amount": int,
            "amount0": int,
            "amount1": int,
        }
        df_mint = pd.read_csv(f'{folder}mint_{pool.name}.csv', converters=mints_converters)

        burns_converts = {
            "block_time": int,
            "block_number": int,
            "tick_lower": int,
            "tick_upper": int,
            "amount": int,
            "amount0": int,
            "amount1": int,
        }
        df_burn = pd.read_csv(f'{folder}burn_{pool.name}.csv', converters=burns_converts)

        swap_converters = {
            "block_time": int,
            "block_number": int,
            "sqrt_price_x96": int,
            "amount0": int,
            "amount1": int,
            "liquidity": int,
        }
        df_swap = pd.read_csv(f'{folder}swap_{pool.name}.csv', converters=swap_converters)
        return cls(pool, df_mint, df_burn, df_swap)

    def preprocess(self) -> None:
        self.mints = self.preprocess_mints(self.mints)
        self.burns = self.preprocess_burns(self.burns)
        self.swaps = self.preprocess_swaps(self.swaps)
        return None

    def preprocess_mints(self, df: pd.DataFrame) -> pd.DataFrame:
        df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
        df = df.set_index('timestamp')
        df = df.sort_values(by=['timestamp', 'amount'], ascending=[True, False])
        df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
        df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
        df['amount'] = df['amount'] / 10**(-self.pool.decimals_diff)
        return df

    def preprocess_burns(self, df: pd.DataFrame) -> pd.DataFrame:
        df['timestamp'] = pd.to_datetime(df["block_time"], unit="s")
        df = df.set_index('timestamp')
        df = df.sort_values(by=['timestamp', 'amount'], ascending=[True, False])
        df['amount0'] = df['amount0'] / 10**self.pool.token0.decimals
        df['amount1'] = df['amount1'] / 10**self.pool.token1.decimals
        df['amount'] = df['amount'] / 10**(-self.pool.decimals_diff)
        return df

    def preprocess_swaps(self, df: pd.DataFrame) -> pd.DataFrame:
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
        df["price_before"] = df["price_before"].fillna(df["price"])

        return df

    def plot(self):
        spot_prices = self.swaps[['price']].resample('D').mean()
        daily_mints = self.mints[['amount']].resample('D').sum()
        daily_burns = self.burns[['amount']].resample('D').sum()
        daily_liq = daily_mints - daily_burns
        total_liq = daily_liq.cumsum()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=spot_prices.index,
                y=spot_prices['price'],
                name="Price",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=total_liq.index,
                y=total_liq['amount'],
                name='Liquidity',
                yaxis='y2',

            ), secondary_y=True)
        # Set x-axis title
        fig.update_xaxes(title_text="Timeline")
        # Set y-axes titles
        fig.update_yaxes(title_text="Price", secondary_y=False)
        fig.update_yaxes(title_text='Liquidity', secondary_y=True)
        fig.update_layout(title='Price and Liquidity')
        return fig
