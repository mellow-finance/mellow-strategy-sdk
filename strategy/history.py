import pandas as pd
import polars as pl
import numpy as np
import datetime
from typing import Hashable
from strategy import log


class PortfolioHistory:
    """
    ``PortfolioHistory`` tracks position stats over time.

    Each time ``add_snapshot`` method is called it remembers current state in time.
    All tracked values then can be accessed via ``to_df`` method that will return a ``pd.Dataframe``.
    """
    def __init__(self):
        self.snapshots = []

    def add_snapshot(self, snapshot: dict):
        """
        Add portfolio snapshot to history.

        Args:
            snapshot: Dict of portfolio params.
        """
        if snapshot:
            self.snapshots.append(snapshot)

    def to_df(self):
        """
        Transform list of portfolio snapshots to data frame.

        Returns:
            Portfolio history data frame.
        """
        log.info('Starting to construct dataframe', length=len(self.snapshots))
        df = pd.DataFrame(self.snapshots)
        df2 = pl.from_pandas(df)
        return df2

    def calculate_values(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate value of portfolio in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio values in X and Y data frame.
        """
        log.info('Starting to calculate values')
        value_of_x_cols = [col for col in df.columns if 'value_x' in col]
        value_of_y_cols = [col for col in df.columns if 'value_y' in col]

        df_x = df[value_of_x_cols].sum(axis=1).alias('total_value_x')
        df_y = df[value_of_y_cols].sum(axis=1).alias('total_value_y')
        return pl.DataFrame([df_x, df_y])

    def calculate_ils(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate IL of portfolio in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio ILs in X and Y data frame.
        """
        log.info('Starting to calculate ils')
        il_to_x_cols = [col for col in df.columns if 'il_x' in col]
        il_to_y_cols = [col for col in df.columns if 'il_y' in col]

        if il_to_x_cols:
            df_x = df[il_to_x_cols].fill_null('forward').sum(axis=1).alias('total_il_x')
            df_y = df[il_to_y_cols].fill_null('forward').sum(axis=1).alias('total_il_y')
        else:
            data = [0] * df.shape[0]
            df_x = pl.Series('total_il_x', data, dtype=pl.Float64)
            df_y = pl.Series('total_il_y', data, dtype=pl.Float64)
        return pl.DataFrame([df_x, df_y])

    def calculate_fees(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate fees of Uniswap positions in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio fees in X and Y data frame.
        """
        log.info('Starting to calculate fees')
        fees_to_x_cols = [col for col in df.columns if 'fees_x' in col]
        fees_to_y_cols = [col for col in df.columns if 'fees_y' in col]
        if fees_to_x_cols:
            df_x = df[fees_to_x_cols].fill_null('forward').sum(axis=1).alias('total_fees_x')
            df_y = df[fees_to_y_cols].fill_null('forward').sum(axis=1).alias('total_fees_y')
        else:
            data = [0] * df.shape[0]
            df_x = pl.Series('total_fees_x', data, dtype=pl.Float64)
            df_y = pl.Series('total_fees_y', data, dtype=pl.Float64)
        return pl.DataFrame([df_x, df_y])

    def calculate_value_to(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate total value of portfolio denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio total value of portfolio denominated in X and Y data frame.
        """
        log.info('Starting to calculate portfolio values')
        df_to = df.select([
            (pl.col('total_value_x') + pl.col('total_value_y') / pl.col('price')).alias('total_value_to_x'),
            (pl.col('total_value_x') * pl.col('price') + pl.col('total_value_y')).alias('total_value_to_y'),
            (pl.col('total_fees_x') + pl.col('total_fees_y') / pl.col('price')).alias('total_fees_to_x'),
            (pl.col('total_fees_x') * pl.col('price') + pl.col('total_fees_y')).alias('total_fees_to_y'),
            (pl.col('total_il_x') + pl.col('total_il_y') / pl.col('price')).alias('total_il_to_x'),
            (pl.col('total_il_x') * pl.col('price') + pl.col('total_il_y')).alias('total_il_to_y'),
            (pl.col('total_value_x').first() + pl.col('total_value_y').first() / pl.col('price')).alias('hold_to_x'),
            (pl.col('total_value_x').first() * pl.col('price') + pl.col('total_value_y').first()).alias('hold_to_y'),
        ])
        return df_to

    def calculate_returns(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate portfolio returns.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio returns data frame.
        """
        log.info('Starting to calculate portfolio returns')
        df_returns = df.select(
            [
                (
                    pl.col('total_value_to_x') /
                    pl.col('total_value_to_x')
                    .shift_and_fill(1, pl.col('total_value_to_x').first())
                ).alias('portfolio_returns_x'),
                (
                    pl.col('total_value_to_y') /
                    pl.col('total_value_to_y')
                    .shift_and_fill(1, pl.col('total_value_to_y').first())
                ).alias('portfolio_returns_y'),
                (
                    pl.col('hold_to_x') /
                    pl.col('hold_to_x')
                    .shift_and_fill(1, pl.col('hold_to_x').first())
                ).alias('hold_returns_x'),
                (
                    pl.col('hold_to_y') /
                    pl.col('hold_to_y')
                    .shift_and_fill(1, pl.col('hold_to_y').first())
                ).alias('hold_returns_y'),
            ]
        )
        return df_returns

    def calculate_apy_for_col(self, df: pl.DataFrame, from_col: str, to_col: str) -> pl.DataFrame:
        """
        Calculate portfolio APY.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio APY data frame.
        """
        log.info(f'Starting to calculate portfolio APY for {from_col}')
        df_performance = df.select([
            pl.col(from_col).cumprod().alias('performance'),
            # pl.col('total_value_to_x') / pl.col('total_value_to_x').first(),
            ((pl.col('timestamp') - pl.col('timestamp').first()).dt.days() + 1).alias('days')
        ])
        df_apy = df_performance.apply(lambda x: x[0] ** (365 / x[1]) - 1)
        df_apy = df_apy.rename({"apply": to_col})
        return df_apy

    def calculate_stats(self) -> pl.DataFrame:
        """
        Calculate all statistics for portfolio.

        Returns:
            Portfolio history data frame.
        """
        df = self.to_df()
        values = self.calculate_values(df)
        ils = self.calculate_ils(df)
        fees = self.calculate_fees(df)

        df_prep = pl.concat([df[['timestamp', 'price']], values, ils, fees], how='horizontal')
        df_to = self.calculate_value_to(df_prep)
        df_returns = self.calculate_returns(df_to)

        df_returns_ext = pl.concat([df[['timestamp']], df_returns], how='horizontal')
        prt_x = self.calculate_apy_for_col(df_returns_ext, 'portfolio_returns_x', 'portfolio_apy_x')
        prt_y = self.calculate_apy_for_col(df_returns_ext, 'portfolio_returns_y', 'portfolio_apy_y')
        hld_x = self.calculate_apy_for_col(df_returns_ext, 'hold_returns_x', 'hold_apy_x')
        hld_y = self.calculate_apy_for_col(df_returns_ext, 'hold_returns_y', 'hold_apy_y')

        return pl.concat([df_prep, df_to, df_returns, prt_x, prt_y, hld_x, hld_y], how='horizontal')


class RebalanceHistory:
    """
       ``RebalanceHistory`` tracks rebalances over time.

       Each time ``add_snapshot`` method is called it remembers rebalance.
       All tracked values then can be accessed via ``to_df`` method that will return a ``pd.Dataframe``.
    """

    def __init__(self):
        self.rebalances = {}

    def add_snapshot(self, timestamp: datetime.datetime, snapshot: Hashable):
        """
        Add portfolio rebalance snapshot to history

        Args:
            timestamp: Timestamp of snapshot.
            snapshot: Dict of portfolio rebalances.
        """
        self.rebalances[timestamp] = snapshot
        return None

    def to_df(self) -> pd.DataFrame:
        """
        Transform list of portfolio rebalance snapshots to data frame.

        Returns:
            Portfolio rebalance history data frame.
        """
        df = pd.DataFrame([self.rebalances], index=['rebalanced']).T
        df.index.name = 'timestamp'
        return df


class UniPositionsHistory:
    """
    ``UniPositionsHistory`` tracks Uniswap positions over time.
    Each time ``add_snapshot`` method is called it remembers all Uniswap positions at current time.
    All tracked values then can be accessed via ``to_df`` method that will return a ``pd.Dataframe``.
    """

    def __init__(self):
        self.positions = {}

    def add_snapshot(self, timestamp: datetime.datetime, positions: dict):
        """
        Add Uniswap position snapshot to history.

        Args:
            timestamp: Timestamp of snapshot.
            positions: List of Uniswap positions.
        """
        uni_positions = {}
        for name, position in positions.items():
            if 'Uni' in name:
                uni_positions[(name, 'lower_bound')] = position.lower_price
                uni_positions[(name, 'upper_bound')] = position.upper_price
        if uni_positions:
            self.positions[timestamp] = uni_positions
        return None

    def to_df(self) -> pd.DataFrame:
        """
        Transform list of Uniswap positions snapshots to data frame.

        Returns:
            Uniswap positions history data frame.
        """
        intervals_df = pd.DataFrame(self.positions).T
        intervals_df.columns = pd.MultiIndex.from_tuples(intervals_df.columns, names=["pos_name", "bound_type"])
        intervals_df.index.name = 'date'
        return intervals_df

    def get_coverage(self, swaps_df: pd.DataFrame) -> float:
        """
        Get coverage metric for all Uniswap positions in historic portfolio.

        Args:
            swaps_df: UniswapV3 exchange data.

        Returns:
            Uniswap positions history data frame.
        """
        prices = swaps_df[['price']]
        prices['covered'] = np.nan

        intervals = self.to_df()
        prices_sliced = prices.loc[intervals.index]['price']

        min_bound = intervals.loc[:, intervals.columns.get_level_values(level=1) == 'lower_bound']
        max_bound = intervals.loc[:, intervals.columns.get_level_values(level=1) == 'upper_bound']

        min_bound.columns = list(min_bound.columns.droplevel(1))
        max_bound.columns = list(max_bound.columns.droplevel(1))

        min_mask = min_bound.lt(prices_sliced, axis=0).any(axis=1)
        max_mask = max_bound.gt(prices_sliced, axis=0).any(axis=1)

        final_mask = min_mask & max_mask

        prices.loc[intervals.index, 'covered'] = final_mask
        prices.loc[:, 'covered'] = prices['covered'].fillna(False)
        coverage = prices['covered'].sum() / prices.shape[0]

        return coverage
