import copy
from typing import Tuple
import polars as pl
from tqdm import tqdm


from mellow_sdk.strategies import AbstractStrategy
from mellow_sdk.portfolio import Portfolio
from mellow_sdk.history import PortfolioHistory, RebalanceHistory, UniPositionsHistory


class Backtest:
    """
    | ``Backtest`` emulate portfolio behavior on historical data.
    | Collects and process portfolio state for each event in historical data.
    | Returns in a convenient form for analyzing the results
    """
    def __init__(
        self,
        strategy: AbstractStrategy,
        portfolio: Portfolio = None,
        by_block=False,
        every_block=False,
    ) -> None:

        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio

        self.by_block = by_block
        self.every_block = every_block

        self.strategy = strategy

    def backtest(
            self,
            df: pl.DataFrame,
    ) -> Tuple[PortfolioHistory, RebalanceHistory, UniPositionsHistory]:
        """
        | 1) Calls ``AbstractStrategy.rebalance`` for every market action with.
        | 2) The return of ``AbstractStrategy.rebalance`` is a name of strategy action e.g.
        | 'init', 'rebalance', 'stop', 'some_cool_action', None. When there is no strategy action ``rebalance`` returns None.
        | 3) Add Strategy action to ``RebalanceHistory``
        | 4) Add Porfolio snapshot to ``PortfolioHistory``
        | 5) Add Porfolio snapshot to ``UniPositionsHistory``
        |
        | You can call ``AbstractStrategy.rebalance`` with any arguments, as it takes *args, **kwargs.
        | Note that 'timestamp', 'price' and 'portfolio' is required.

        Attributes:
            df: df with pool events, or df with market data. df format is [('timestamp': datetime, 'price' : float)]
            by_block: False - backtest on every action in mempool, True - backtest every block
            every_block: False - skip blocks without actions, otherwise bt return last action for every block.
        Returns:
            | History classes that store different portfolio stapshots.
            |
            | ``PortfolioHistory`` - keeps portfolio snapshots such as: value, fees, etc.
            | ``RebalanceHistory`` - keeps strategy actions, such as init ot rebalances.
            | ``UniPositionsHistory`` -  keeps information about opened UniV3 positions.
        """
        portfolio_history = PortfolioHistory()
        rebalance_history = RebalanceHistory()
        uni_history = UniPositionsHistory()

        if (self.by_block or self.every_block) and ('block_number' in df.columns):
            maxs = df.groupby(['block_number']).agg({'timestamp': 'max'})

            df = df.join(maxs, on=['block_number'])
            df = df[df['timestamp'] == df['timestamp_max']].drop('timestamp_max')

        if self.every_block and ('block_number' in df.columns):
            all_blocks = pl.DataFrame({'block_number': range(df['block_number'].min(), df['block_number'].max())})

            df = all_blocks.join(df, on=['block_number'], how='left')
            df = df.with_column(df['event'].fill_null(0).alias('event')).fill_null(strategy='forward')

        for record in df.to_dicts():
            is_rebalanced = self.strategy.rebalance(record=record, portfolio=self.portfolio)
            portfolio_snapshot = self.portfolio.snapshot(
                timestamp=record['timestamp'],
                price=record['price'],
                block_number=record.get('price', None)
            )
            portfolio_history.add_snapshot(portfolio_snapshot)
            rebalance_history.add_snapshot(record['timestamp'], is_rebalanced)
            uni_history.add_snapshot(record['timestamp'], copy.copy(self.portfolio.positions))

        return portfolio_history, rebalance_history, uni_history


class BacktestTimeCV:
        """
        | ``Backtest`` emulate portfolio behavior on historical data.
        | Collects and process portfolio state for each event in historical data.
        | Returns in a convenient form for analyzing the results
        """

        def __init__(
            self,
            strategy: AbstractStrategy,
            portfolio: Portfolio = None,
            by_block=False,
            every_block=False
        ) -> None:

            if portfolio is None:
                self.portfolio = Portfolio('main')
            else:
                self.portfolio = portfolio

            self.by_block = by_block
            self.every_block = every_block

            self.strategy = strategy

        def get_splits(self, df, test_sec, step_sec):
            idx_column = df.with_row_count()['row_nr']
            ts_col = df['timestamp'].cast(int)

            test_idx = []
            test_sec *= 10 ** 6
            step_sec *= 10 ** 6

            left_bound = ts_col.min()
            right_bound = ts_col.min() + test_sec

            while right_bound < ts_col.max():
                idx = idx_column[(ts_col >= left_bound) & (ts_col < right_bound)]
                test_idx.append(idx)

                left_bound += step_sec
                right_bound += step_sec
            return test_idx

        def get_tail_splits(self, df, min_test_sec, step_sec):
            idx_column = df.with_row_count()['row_nr']
            ts_col = df['timestamp'].cast(int)

            test_idx = []
            min_test_sec *= 10 ** 6
            step_sec *= 10 ** 6

            right_bound = ts_col.min() + min_test_sec

            while right_bound < ts_col.max():
                idx = idx_column[ts_col < right_bound]
                test_idx.append(idx)

                right_bound += step_sec
            return test_idx

        def backtest(self, df, test_sec, step_sec, tail_type_cv=False):
            metrics = None
            if tail_type_cv:
                folds = self.get_tail_splits(df, min_test_sec=test_sec, step_sec=step_sec)
            else:
                folds = self.get_splits(df, test_sec=test_sec, step_sec=step_sec)

            assert len(folds) > 0, 'there is no folds, change yours parameters'

            realized_folds = []
            for fold_num, test_idx in enumerate(tqdm(folds)):
                df_test = df[test_idx]
                bt = Backtest(
                    strategy=copy.copy(self.strategy),
                    by_block=self.by_block,
                    every_block=self.every_block
                )

                if df_test.shape[0] == 0:
                    print(f'fold {fold_num} is empty, fold will be skipped')
                else:
                    portfolio_history, rebalance_history, uni_history = bt.backtest(df=df_test)
                    stats = portfolio_history.calculate_stats()

                    stats = stats.with_columns([
                        pl.col('timestamp').first().alias('fold_from'),
                        pl.col('timestamp').last().alias('fold_to'),
                    ])

                    if metrics is None:
                        metrics = stats[-1]
                    else:
                        metrics = metrics.vstack(stats[-1])

                    realized_folds.append(fold_num)

            metrics = metrics.with_column(
                pl.Series(realized_folds).alias('fold_num')
            )
            return metrics


class BacktestBlockCV:
    """
    | ``Backtest`` emulate portfolio behavior on historical data.
    | Collects and process portfolio state for each event in historical data.
    | Returns in a convenient form for analyzing the results
    """

    def __init__(
            self,
            strategy: AbstractStrategy,
            portfolio: Portfolio = None,
            by_block = False,
            every_block = False
    ) -> None:

        if portfolio is None:
            self.portfolio = Portfolio('main')
        else:
            self.portfolio = portfolio

        self.by_block = by_block
        self.every_block = every_block

        self.strategy = strategy

    def get_splits(self, df, test_blocks, step_blocks):
        idx_column = df.with_row_count()['row_nr']
        ts_col = df['block_number']

        test_idx = []

        left_bound = ts_col.min()
        right_bound = ts_col.min() + test_blocks

        while right_bound < ts_col.max():
            idx = idx_column[(ts_col >= left_bound) & (ts_col < right_bound)]
            test_idx.append(idx)

            left_bound += step_blocks
            right_bound += step_blocks
        return test_idx

    def get_tail_splits(self, df, min_test_blocks, step_blocks):
        idx_column = df.with_row_count()['row_nr']
        ts_col = df['block_number']

        test_idx = []

        right_bound = ts_col.min() + min_test_blocks

        while right_bound < ts_col.max():
            idx = idx_column[ts_col < right_bound]
            test_idx.append(idx)

            right_bound += step_blocks
        return test_idx

    def backtest(self, df, test_blocks, step_blocks, tail_type_cv=False):
        metrics = None
        if tail_type_cv:
            folds = self.get_tail_splits(df, min_test_blocks=test_blocks, step_blocks=step_blocks)
        else:
            folds = self.get_splits(df, test_blocks=test_blocks, step_blocks=step_blocks)

        assert len(folds) > 0, 'there is no folds, change yours parameters'

        realized_folds = []
        for fold_num, test_idx in enumerate(tqdm(folds)):
            df_test = df[test_idx]
            bt = Backtest(
                strategy=copy.copy(self.strategy),
                by_block = self.by_block,
                every_block = self.every_block
            )

            if df_test.shape[0] == 0:
                print(f'fold {fold_num} is empty, fold will be skipped')
            else:
                portfolio_history, rebalance_history, uni_history = bt.backtest(df=df_test)
                stats = portfolio_history.calculate_stats()

                stats = stats.with_columns([
                    pl.col('timestamp').first().alias('fold_from'),
                    pl.col('timestamp').last().alias('fold_to'),
                ])

                if metrics is None:
                    metrics = stats[-1]
                else:
                    metrics = metrics.vstack(stats[-1])

                realized_folds.append(fold_num)

        metrics = metrics.with_column(
            pl.Series(realized_folds).alias('fold_num')
        )
        return metrics