import pandas as pd
import polars as pl
import datetime
import typing as tp


class PortfolioHistory:
    """
    | ``PortfolioHistory`` accumulate snapshots and can calculate stats over time from snapshots.
    | Each time ``add_snapshot`` method is called it remembers current state in time.
    | All tracked values then can be accessed via ``to_df`` method that will return a ``pl.Dataframe``.
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
            Calculate amount of X and amount of Y in ``Portfolio``.

            Args:
                df: Portfolio history DataFrame.

            Returns:
                dataframe consisting of two columns total_value_x, total_value_y.
        """

        value_of_x_cols = [col for col in df.columns if 'value_x' in col]
        value_of_y_cols = [col for col in df.columns if 'value_y' in col]

        df_x = df[value_of_x_cols].sum(axis=1).alias('total_value_x')
        df_y = df[value_of_y_cols].sum(axis=1).alias('total_value_y')
        return pl.DataFrame([df_x, df_y])

    def calculate_ils(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        | Calculate impermanent loss separately in X and Y currencies as sum of positions IL.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Dataframe consisting of two columns total_il_x, total_il_y.
        """
        # log.info('Starting to calculate ils')
        il_to_x_cols = [col for col in df.columns if 'il_to_x' in col]
        il_to_y_cols = [col for col in df.columns if 'il_to_y' in col]

        if il_to_x_cols:
            df_x = df[il_to_x_cols].fill_null('forward').sum(axis=1).alias('total_il_to_x')
            df_y = df[il_to_y_cols].fill_null('forward').sum(axis=1).alias('total_il_to_y')
        else:
            data = [0] * df.shape[0]
            df_x = pl.Series('total_il_to_x', data, dtype=pl.Float64)
            df_y = pl.Series('total_il_to_y', data, dtype=pl.Float64)
        return pl.DataFrame([df_x, df_y])

    def calculate_fees(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        | Calculate X and Y fees of Uniswap positions as sum over all positions.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Dataframe consisting of two columns total_fees_x, total_fees_y.
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
        | Calculates:
        | total_value_to_x - total_value denominated in X,
        | total_value_to_y - total_value denominated in Y,
        | total_fees_to_x - total_fees denominated in X,
        | total_fees_to_y - total_fees denominated in Y,
        | hold_to_x - total_value denominated in X for corresponding hold strategy,
        | hold_to_y - total_value denominated in Y for corresponding hold strategy.

        Args:
            df:
                Portfolio history DataFrame with cols from ``PortfolioHistory.calculate_values``,
                ``PortfolioHistory.calculate_ils``, ``PortfolioHistory.calculate_fees``.

        Returns:
            Dataframe consisting of 'total_value_...' columns.
        """
        # log.info('Starting to calculate portfolio values')
        df_to = df.select([
            (pl.col('total_value_x') + pl.col('total_value_y') / pl.col('price')).alias('total_value_to_x'),
            (pl.col('total_value_x') * pl.col('price') + pl.col('total_value_y')).alias('total_value_to_y'),
            (pl.col('total_fees_x') + pl.col('total_fees_y') / pl.col('price')).alias('total_fees_to_x'),
            (pl.col('total_fees_x') * pl.col('price') + pl.col('total_fees_y')).alias('total_fees_to_y'),
            (pl.col('total_value_x').first() + pl.col('total_value_y').first() / pl.col('price')).alias('hold_to_x'),
            (pl.col('total_value_x').first() * pl.col('price') + pl.col('total_value_y').first()).alias('hold_to_y'),
        ])
        return df_to

    def calculate_apy_for_col(self, df: pl.DataFrame, from_col: str, to_col: str) -> pl.DataFrame:
        """
            Calculate APY for metric.

        Args:
            df: Dataframe with metrics.
            from_col: Metric column name.
            to_col: Name for new column with metric's APY.

        Returns:
            Dataframe consisting APY metric.
        """

        df_performance = df.select([
                (pl.col(from_col) / pl.col(from_col).first()).alias('performance'),
                ((pl.col('timestamp') - pl.col('timestamp').first()).dt.days()).alias('days')
            ])
        df_apy = df_performance.apply(lambda x: 100 * (x[0] ** (365 / x[1]) - 1) if x[1] != 0 else 0.)
        df_apy = df_apy.rename({'apply': to_col})
        return df_apy

    def calculate_g_apy(self, df: pl.DataFrame) -> pl.DataFrame:
        """
            Calculate gAPY. gAPY is a strategy profitability metric,
            which means how much a portfolio value is better than simple holding.
            More details can be found here:
            https://twitter.com/0xAlexEuler/status/1503444182257393666?s=20&t=VyzSBZEemZZIxc3AalXqQA

        Args:
            df: Dataframe with total_value_to, hold_to_x.

        Returns:
            Dataframe consisting gAPY metric.
        """

        df2 = df.select([
                (pl.col('total_value_to_x') / pl.col('hold_to_x')).alias('coef'),
                ((pl.col('timestamp') - pl.col('timestamp').first()).dt.days()).alias('days'),
        ])

        df_apy = df2.apply(lambda x: 100 * (x[0] ** (365 / x[1]) - 1) if x[1] != 0 else 0.)
        df_apy = df_apy.rename({"apply": 'g_apy'})
        return df_apy

    def calculate_stats(self) -> pl.DataFrame:
        """
        Calculate all statistics for portfolio. Main function of class.

        Returns:
            Portfolio statistics dataframe.
        """
        df = self.to_df()
        values = self.calculate_values(df)
        ils = self.calculate_ils(df)
        fees = self.calculate_fees(df)

        df_prep = pl.concat([df[['timestamp', 'price']], values, ils, fees], how='horizontal')
        df_to = self.calculate_value_to(df_prep)
        df_to_ext = pl.concat([df[['timestamp']], df_to], how='horizontal')

        prt_x = self.calculate_apy_for_col(df_to_ext, 'total_value_to_x', 'portfolio_apy_x')
        prt_y = self.calculate_apy_for_col(df_to_ext, 'total_value_to_y', 'portfolio_apy_y')
        hld_x = self.calculate_apy_for_col(df_to_ext, 'hold_to_x', 'hold_apy_x')
        hld_y = self.calculate_apy_for_col(df_to_ext, 'hold_to_y', 'hold_apy_y')
        g_apy = self.calculate_g_apy(df_to_ext)

        return pl.concat([df_prep, df_to, prt_x, prt_y, hld_x, hld_y, g_apy], how='horizontal')


class RebalanceHistory:
    """
    | ``RebalanceHistory`` tracks Strategy actions (portfolio rebalances) over time.
    | Each time ``add_snapshot`` method is called class remembers action.
    | All actions can be accessed via ``to_df`` method that will return a ``pl.Dataframe``.
    """

    def __init__(self):
        self.rebalances = []

    def add_snapshot(self, timestamp: datetime.datetime, portfolio_action: tp.Optional[str]):
        """
        Add portfolio action to memory.

        Args:
            timestamp: Timestamp of snapshot.
            portfolio_action: Name of portfolio action or None. Usually it takes from ''AbstractStrategy.rebalance`` output.
        """
        self.rebalances += [{'timestamp': timestamp, 'rebalance': portfolio_action}]

    def to_df(self) -> pd.DataFrame:
        """
        | Transform list of strategy actions to data frame.

        Returns:
            Data frame of strategy actions, except None actions.
        """
        df = pl.DataFrame([
            pl.Series(name='timestamp', values=[x['timestamp'] for x in self.rebalances]),
            pl.Series(name='rebalance', values=[x['rebalance'] for x in self.rebalances], dtype=pl.Utf8),
        ]).drop_nulls().with_column(pl.col('timestamp').cast(pl.Datetime))
        return df


class UniPositionsHistory:
    """
    ``UniPositionsHistory`` tracks UniswapV3 positions over time.
    Each time ``add_snapshot`` method is called it remembers all UniswapV3 positions at current time.
    All tracked values then can be accessed via ``to_df`` method that will return a ``pl.Dataframe``.
    """

    def __init__(self):
        self.positions = []

    def add_snapshot(self, timestamp: datetime.datetime, positions: dict) -> None:
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
        if len(self.positions) == 0:
            intervals_df = pl.DataFrame(
                {'name': [], 'timestamp': [], 'lower_bound': [], 'upper_bound': [], 'liq': []}
            )
        else:
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
    #     pass
    #     return coverage
