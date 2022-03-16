import pandas as pd
import polars as pl
import numpy as np
import datetime
from typing import Hashable


class PortfolioHistory:
    """
    | ``PortfolioHistory`` accumulate snapshots and can calculate stats over time from snapshots.
    | Each time ``add_snapshot`` method is called it remembers current state in time.
    | All tracked values then can be accessed via ``to_df`` method that will return a ``pd.Dataframe``.
    """
    def __init__(self):
        self.snapshots = []

    def add_snapshot(self, snapshot: dict) -> None:
        """
        Add portfolio snapshot to history.

        Args:
            snapshot: Dict of portfolio params.
        """
        if snapshot:
            self.snapshots.append(snapshot)

    def to_df(self) -> pl.DataFrame:
        """
        Transform list of portfolio snapshots to data frame.

        Returns:
            Portfolio history data frame.
        """
        df = pd.DataFrame(self.snapshots)
        df2 = pl.from_pandas(df).sort(by=['timestamp'])
        return df2

    def calculate_values(self, df: pl.DataFrame) -> pl.DataFrame:
        """
            Calculate amount of X and amount of Y in ``Portfolio``

            Args:
                df: Portfolio history DataFrame. return of ``PortfolioHistory.to_df()``

            Returns:
                dataframe consisting of two columns total_value_x, total_value_y
        """

        value_of_x_cols = [col for col in df.columns if 'value_x' in col]
        value_of_y_cols = [col for col in df.columns if 'value_y' in col]

        df_x = df[value_of_x_cols].sum(axis=1).alias('total_value_x')
        df_y = df[value_of_y_cols].sum(axis=1).alias('total_value_y')
        return pl.DataFrame([df_x, df_y])

    def calculate_ils(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        | Calculate impermanent loss separately in X and Y currencies.
        | As sum of positions IL.
        Args:
            df: Portfolio history DataFrame. return of ``PortfolioHistory.to_df()``

        Returns:
            dataframe consisting of two columns total_il_x, total_il_y
        """
        # log.info('Starting to calculate ils')
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
        | Calculate X and Y fees of Uniswap positions.
        | As sum over all positions

        Args:
            df: Portfolio history DataFrame. return of ``PortfolioHistory.to_df()``

        Returns:
            dataframe consisting of two columns total_fees_x, total_fees_y
        """
        # log.info('Starting to calculate fees')
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
        | Calculate:
        | total_value_to_x - total_value denominated in X
        | total_fees_to_x - total_fees denominated in X
        | total_il_to_x - total_il denominated in X
        | hold_to_x - total_value denominated in X for hold strategy
        | corresponding columns with  denomination in Y
        | vpn_value - total_value_to_x at last price p_n
        | vpn_hold - hold_to_x at last price p_n

        Args:
            df:
                Portfolio history DataFrame with cols from ``PortfolioHistory.calculate_values``,
                ``PortfolioHistory.calculate_ils``, ``PortfolioHistory.calculate_fees``

        Returns:
            dataframe consisting of new columns
        """
        # log.info('Starting to calculate portfolio values')
        df_to = df.select([
            (pl.col('total_value_x') + pl.col('total_value_y') / pl.col('price')).alias('total_value_to_x'),
            (pl.col('total_value_x') * pl.col('price') + pl.col('total_value_y')).alias('total_value_to_y'),
            (pl.col('total_fees_x') + pl.col('total_fees_y') / pl.col('price')).alias('total_fees_to_x'),
            (pl.col('total_fees_x') * pl.col('price') + pl.col('total_fees_y')).alias('total_fees_to_y'),
            (pl.col('total_il_x') + pl.col('total_il_y') / pl.col('price')).alias('total_il_to_x'),
            (pl.col('total_il_x') * pl.col('price') + pl.col('total_il_y')).alias('total_il_to_y'),
            (pl.col('total_value_x').first() + pl.col('total_value_y').first() / pl.col('price')).alias('hold_to_x'),
            (pl.col('total_value_x').first() * pl.col('price') + pl.col('total_value_y').first()).alias('hold_to_y'),
            (pl.col('total_value_x') + pl.col('total_value_y') / pl.col('price').last()).alias('vpn_value'),
            (pl.col('total_value_x').first() + pl.col('total_value_y').first() / pl.col('price').last()).alias('vpn_hold'),
        ])
        return df_to

    def calculate_returns(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        | Calculate: returns for columns.
        | new columns:
        | portfolio_returns_x, hold_returns_x
        | portfolio_returns_y, hold_returns_y
        | vpn_returns
        | vpn_hold_returns

        Args:
            df: Portfolio history DataFrame.

        Returns:
            dataframe consisting of new columns
        """
        # log.info('Starting to calculate portfolio returns')
        df_returns = df.select([
                (
                    pl.col('total_value_to_x') /
                    pl.col('total_value_to_x').shift_and_fill(1, pl.col('total_value_to_x').first())
                ).alias('portfolio_returns_x'),
                (
                    pl.col('total_value_to_y') /
                    pl.col('total_value_to_y').shift_and_fill(1, pl.col('total_value_to_y').first())
                ).alias('portfolio_returns_y'),
                (
                    pl.col('hold_to_x') /
                    pl.col('hold_to_x').shift_and_fill(1, pl.col('hold_to_x').first())
                ).alias('hold_returns_x'),
                (
                    pl.col('hold_to_y') /
                    pl.col('hold_to_y').shift_and_fill(1, pl.col('hold_to_y').first())
                ).alias('hold_returns_y'),
                (
                    pl.col('vpn_value') /
                    pl.col('vpn_value').shift_and_fill(1, pl.col('vpn_value').first())
                ).alias('vpn_returns'),
                (
                    pl.col('vpn_hold') /
                    pl.col('vpn_hold').shift_and_fill(1, pl.col('vpn_hold').first())
                ).alias('vpn_hold_returns'),
        ])
        return df_returns

    def calculate_apy_for_col(self, df: pl.DataFrame, from_col: str, to_col: str,
                              calculate_full: bool = False) -> pl.DataFrame:
        """
            Calculate APY for metric
        Args:
            df: dataframe with metrics
            from_col: metric column name
            to_col: name for new column with metric APY
            calculate_full:
                | True: calculate APY from first day to last
                | False: calculate APY from first day to current

        Returns:
            dataframe consisting of 'to_col' column
        """

        if calculate_full:
            df_performance = df.select([
                (pl.col(from_col) / pl.col(from_col).first()).alias('performance'),
                ((pl.col('timestamp').last() - pl.col('timestamp').first()).dt.days()).alias('days')
            ])
        else:
            df_performance = df.select([
                (pl.col(from_col) / pl.col(from_col).first()).alias('performance'),
                ((pl.col('timestamp') - pl.col('timestamp').first()).dt.days()).alias('days')
            ])

        df_apy = df_performance.apply(lambda x: 100 * (x[0] ** (365 / x[1]) - 1) if x[1] != 0 else 0.)

        df_apy = df_apy.rename({"apply": to_col})
        return df_apy

    def calculate_stats(self) -> pl.DataFrame:
        """
        Calculate all statistics for portfolio. Main function of class.

        Returns:
            Portfolio history data frame.
        """
        df = self.to_df()
        values = self.calculate_values(df)
        ils = self.calculate_ils(df)
        fees = self.calculate_fees(df)

        df_prep = pl.concat([df[['timestamp', 'price']], values, ils, fees], how='horizontal')
        df_to = self.calculate_value_to(df_prep)
        # df_returns = self.calculate_returns(df_to)
        df_to_ext = pl.concat([df[['timestamp']], df_to], how='horizontal')

        prt_x = self.calculate_apy_for_col(df_to_ext, 'total_value_to_x', 'portfolio_apy_x')
        prt_y = self.calculate_apy_for_col(df_to_ext, 'total_value_to_y', 'portfolio_apy_y')
        hld_x = self.calculate_apy_for_col(df_to_ext, 'hold_to_x', 'hold_apy_x')
        hld_y = self.calculate_apy_for_col(df_to_ext, 'hold_to_y', 'hold_apy_y')
        vpn_apy = self.calculate_apy_for_col(df_to_ext, 'vpn_value', 'vpn_apy')

        return pl.concat([df_prep, df_to, prt_x, prt_y, hld_x, hld_y, vpn_apy], how='horizontal')


class RebalanceHistory:
    # TODO docs
    """
       ``RebalanceHistory`` tracks rebalances over time.

       Each time ``add_snapshot`` method is called it remembers rebalance.
       All tracked values then can be accessed via ``to_df`` method that will return a ``pd.Dataframe``.
    """

    def __init__(self):
        self.rebalances = []

    def add_snapshot(self, timestamp: datetime.datetime, snapshot: Hashable):
        """
        Add portfolio rebalance snapshot to history

        Args:
            timestamp: Timestamp of snapshot.
            snapshot: Dict of portfolio rebalances.
        """
        self.rebalances += [{'timestamp': timestamp, 'rebalance': snapshot}]
        return None

    def to_df(self) -> pd.DataFrame:
        """
        Transform list of portfolio rebalance snapshots to data frame.

        Returns:
            Portfolio rebalance history data frame.
        """
        df = (
            pl.DataFrame(self.rebalances)
            .drop_nulls()
            .with_column(
                pl.col('timestamp')
                .cast(pl.Datetime)
            )
        )
        return df


class UniPositionsHistory:
    # TODO docs
    """
    ``UniPositionsHistory`` tracks Uniswap positions over time.
    Each time ``add_snapshot`` method is called it remembers all Uniswap positions at current time.
    All tracked values then can be accessed via ``to_df`` method that will return a ``pd.Dataframe``.
    """

    def __init__(self):
        self.positions = []

    def add_snapshot(self, timestamp: datetime.datetime, positions: dict):
        """
        Add Uniswap position snapshot to history.

        Args:
            timestamp: Timestamp of snapshot.
            positions: List of Uniswap positions.
        """
        for name, position in positions.items():
            if 'Uni' in name:
                record = {
                    'name': name,
                    'timestamp': timestamp,
                    'lower_bound': position.lower_price,
                    'upper_bound': position.upper_price,
                    'liq': position.liquidity,
                }
                self.positions.append(record)

    def to_df(self) -> pl.DataFrame:
        """
        Transform list of Uniswap positions snapshots to data frame.

        Returns:
            Uniswap positions history data frame.
        """
        intervals_df = pl.from_records(self.positions)
        return intervals_df

    # def get_coverage(self, swaps_df: pd.DataFrame) -> float:
    #     """
    #     Get coverage metric for all Uniswap positions in historic portfolio.
    #
    #     Args:
    #         swaps_df: UniswapV3 exchange data.
    #
    #     Returns:
    #         Uniswap positions history data frame.
    #     """
    #     prices = swaps_df[['price']]
    #     prices['covered'] = np.nan
    #
    #     intervals = self.to_df()
    #     prices_sliced = prices.loc[intervals.index]['price']
    #
    #     min_bound = intervals.loc[:, intervals.columns.get_level_values(level=1) == 'lower_bound']
    #     max_bound = intervals.loc[:, intervals.columns.get_level_values(level=1) == 'upper_bound']
    #
    #     min_bound.columns = list(min_bound.columns.droplevel(1))
    #     max_bound.columns = list(max_bound.columns.droplevel(1))
    #
    #     min_mask = min_bound.lt(prices_sliced, axis=0).any(axis=1)
    #     max_mask = max_bound.gt(prices_sliced, axis=0).any(axis=1)
    #
    #     final_mask = min_mask & max_mask
    #
    #     prices.loc[intervals.index, 'covered'] = final_mask
    #     prices.loc[:, 'covered'] = prices['covered'].fillna(False)
    #     coverage = prices['covered'].sum() / prices.shape[0]
    #
    #     return coverage
