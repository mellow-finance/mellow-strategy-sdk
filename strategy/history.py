import pandas as pd
import numpy as np
import datetime
from typing import Hashable


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
        return None

    def to_df(self):
        """
        Transform list of portfolio snapshots to data frame.

        Returns:
            Portfolio history data frame.
        """
        df = pd.DataFrame(self.snapshots)
        df = df.set_index('timestamp')
        return df

    def calculate_value_to(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total value of portfolio denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """
        value_to_x_cols = [col for col in df.columns if 'value_to_x' in col]
        value_to_y_cols = [col for col in df.columns if 'value_to_y' in col]

        df[value_to_x_cols] = df[value_to_x_cols].fillna(0)
        df[value_to_y_cols] = df[value_to_y_cols].fillna(0)

        df['total_value_to_x'] = df[value_to_x_cols].sum(axis=1)
        df['total_value_to_y'] = df[value_to_y_cols].sum(axis=1)
        return df

    def calculate_value(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total value of portfolio in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """
        value_x_cols = [col for col in df.columns if 'value_x' in col]
        value_y_cols = [col for col in df.columns if 'value_y' in col]

        df[value_x_cols] = df[value_x_cols].fillna(0)
        df[value_y_cols] = df[value_y_cols].fillna(0)

        df['total_value_x'] = df[value_x_cols].sum(axis=1)
        df['total_value_y'] = df[value_y_cols].sum(axis=1)
        return df

    def calculate_bicurr_hold(self, df: pd.DataFrame) -> pd.DataFrame:
        df['bicurr_hold_to_x'] = df.iloc[0]['total_value_x'] + df.iloc[0]['total_value_y'] / df['price']
        df['bicurr_hold_to_y'] = df.iloc[0]['total_value_x'] * df['price'] + df.iloc[0]['total_value_y']
        return df

    def calculate_il(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate IL of portfolio denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """
        il_to_x_cols = [col for col in df.columns if 'il_to_x' in col]
        il_to_y_cols = [col for col in df.columns if 'il_to_y' in col]
        if il_to_x_cols:
            df[il_to_x_cols] = df[il_to_x_cols].ffill().fillna(0)
            df[il_to_y_cols] = df[il_to_y_cols].ffill().fillna(0)

            df['total_il_to_x'] = df[il_to_x_cols].sum(axis=1)
            df['total_il_to_y'] = df[il_to_y_cols].sum(axis=1)
        else:
            df['total_il_to_x'] = 0
            df['total_il_to_y'] = 0
        return df

    def calculate_rl(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate IL of portfolio denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """
        rl_to_x_cols = [col for col in df.columns if 'realized_loss_to_x' in col]
        rl_to_y_cols = [col for col in df.columns if 'realized_loss_to_y' in col]

        if rl_to_x_cols:
            df[rl_to_x_cols] = df[rl_to_x_cols].fillna(0)
            df[rl_to_y_cols] = df[rl_to_y_cols].fillna(0)

            df['total_rl_to_x'] = df[rl_to_x_cols].sum(axis=1)
            df['total_rl_to_y'] = df[rl_to_y_cols].sum(axis=1)
        else:
            df['total_rl_to_x'] = 0
            df['total_rl_to_y'] = 0
        return df

    def calculate_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Costs of portfolio management denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
             Portfolio history data frame with new columns.
        """
        costs_cols = [col for col in df.columns if 'total_rebalance_costs' in col]
        if costs_cols:
            df[costs_cols] = df[costs_cols].ffill()
            df[costs_cols] = df[costs_cols].fillna(0)

            df['total_rebalance_costs'] = df[costs_cols].sum(axis=1)
        else:
            df['total_rebalance_costs'] = 0
        return df

    def calculate_liquidity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total liquidity of all Uniswap positions.

        Args:
            df: Portfolio history DataFrame.

        Returns:
             Portfolio history data frame with new columns.
        """
        liq_cols = [col for col in df.columns if 'current_liquidity' in col]

        if liq_cols:
            df[liq_cols] = df[liq_cols].fillna(0)
            df['total_current_liquidity'] = df[liq_cols].sum(axis=1)
        else:
            df['total_current_liquidity'] = 0
            df['total_current_liquidity'] = 0

        return df

    def calculate_actual_fees(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate actual fees of Uniswap positions denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """
        fees_to_x_cols = [col for col in df.columns if 'current_fees_to_x' in col]
        fees_to_y_cols = [col for col in df.columns if 'current_fees_to_y' in col]

        if fees_to_x_cols:
            df[fees_to_x_cols] = df[fees_to_x_cols].fillna(0)
            df[fees_to_y_cols] = df[fees_to_y_cols].fillna(0)

            df['total_current_fees_to_x'] = df[fees_to_x_cols].sum(axis=1)
            df['total_current_fees_to_y'] = df[fees_to_y_cols].sum(axis=1)
        else:
            df['total_current_fees_to_x'] = 0
            df['total_current_fees_to_y'] = 0
        return df

    def calculate_earned_fees(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total erned fees of Uniswap positions denominated in X and Y.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame  with new columns.
        """
        fees_to_x_cols = [col for col in df.columns if 'earned_fees_to_x' in col]
        fees_to_y_cols = [col for col in df.columns if 'earned_fees_to_y' in col]

        if fees_to_x_cols:
            df[fees_to_x_cols] = df[fees_to_x_cols].ffill()
            df[fees_to_y_cols] = df[fees_to_y_cols].ffill()

            df[fees_to_x_cols] = df[fees_to_x_cols].fillna(0)
            df[fees_to_y_cols] = df[fees_to_y_cols].fillna(0)

            df['total_earned_fees_to_x'] = df[fees_to_x_cols].sum(axis=1)
            df['total_earned_fees_to_y'] = df[fees_to_y_cols].sum(axis=1)
        else:
            df['total_earned_fees_to_x'] = 0
            df['total_earned_fees_to_y'] = 0
        return df

    def calculate_porfolio_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate portfolio returns.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """
        df['portfolio_returns_to_x'] = df['portfolio_value_to_x'] / df['portfolio_value_to_x'].shift()
        df['portfolio_returns_to_y'] = df['portfolio_value_to_y'] / df['portfolio_value_to_y'].shift()
        return df

    def calculate_apy_hold(self, df: pd.DataFrame) -> pd.DataFrame:
        def yearly_adj(_df):
            days_gone = (_df.index[-1] - _df.index[0]).days + 1
            out = _df.iloc[-1] ** (365 / days_gone)
            return out

        df['bicurr_returns_to_y'] = df['bicurr_hold_to_y'] / df['bicurr_hold_to_y'].shift()
        df['bicurr_performance_to_y_apy'] = df['bicurr_returns_to_y'].cumprod().expanding().apply(yearly_adj)

        df['bicurr_performance_to_y_apy'] -= 1
        return df

    def calculate_performance_adj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate portfolio performance relative to currency pair.

        Args:
            df: Portfolio history DataFrame.

        Returns:
            Portfolio history data frame with new columns.
        """

        def yearly_adj(_df):
            days_gone = (_df.index[-1] - _df.index[0]).days + 1
            out = _df.iloc[-1] ** (365 / days_gone)
            return out

        df['price_returns_to_y'] = df['price'] / df['price'].shift()
        df['price_returns_to_x'] = df['price'].shift() / df['price']

        df['portfolio_returns_rel_to_x'] = df['portfolio_returns_to_x'] / df['price_returns_to_x']
        df['portfolio_returns_rel_to_y'] = df['portfolio_returns_to_y'] / df['price_returns_to_y']

        df['portfolio_performance_rel_to_x_apy'] = df[
            'portfolio_returns_rel_to_x'].cumprod().expanding().apply(yearly_adj)
        df['portfolio_performance_rel_to_y_apy'] = df[
            'portfolio_returns_rel_to_y'].cumprod().expanding().apply(yearly_adj)

        df['portfolio_performance_rel_to_x_apy'] -= 1
        df['portfolio_performance_rel_to_y_apy'] -= 1
        return df

    def calculate_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate portfolio performance.

        Args:
            df: Portfolio stats DataFrame.

        Returns:
            Portfolio history data frame with new column.
        """

        def yearly_adj(_df):
            days_gone = (_df.index[-1] - _df.index[0]).days + 1
            out = _df.iloc[-1] ** (365 / days_gone)
            return out

        df['portfolio_performance_to_x_apy'] = df['portfolio_returns_to_x'].cumprod().expanding().apply(
            yearly_adj)
        df['portfolio_performance_to_y_apy'] = df['portfolio_returns_to_y'].cumprod().expanding().apply(
            yearly_adj)

        df['portfolio_performance_to_x_apy'] -= 1
        df['portfolio_performance_to_y_apy'] -= 1
        return df

    def portfolio_stats(self) -> pd.DataFrame:
        """
        Calculate all statistics for portfolio.

        Returns:
            Portfolio history data frame.
        """
        df = self.to_df()
        df = self.calculate_value(df)
        df = self.calculate_bicurr_hold(df)
        df = self.calculate_value_to(df)
        df = self.calculate_il(df)
        df = self.calculate_rl(df)
        df = self.calculate_liquidity(df)
        df = self.calculate_actual_fees(df)
        df = self.calculate_earned_fees(df)
        df = self.calculate_costs(df)

        if 'total_current_fees_to_x' in df.columns:
            df['portfolio_value_to_x'] = df['total_value_to_x'] + df['total_current_fees_to_x']
            df['portfolio_value_to_y'] = df['total_value_to_y'] + df['total_current_fees_to_y']
        else:
            df['portfolio_value_to_x'] = df['total_value_to_x']
            df['portfolio_value_to_y'] = df['total_value_to_y']

        if 'total_il_to_x' in df.columns:
            if 'total_rl_to_x' in df.columns:
                df['total_loss_to_x'] = df['total_il_to_x'] + df['total_rl_to_x']
                df['total_loss_to_y'] = df['total_il_to_y'] + df['total_rl_to_y']
            else:
                df['total_loss_to_x'] = df['total_il_to_x']
                df['total_loss_to_y'] = df['total_il_to_y']
        else:
            df['total_loss_to_x'] = 0
            df['total_loss_to_y'] = 0

        if 'total_earned_fees_to_x' not in df.columns:
            df['total_earned_fees_to_x'] = 0
            df['total_earned_fees_to_y'] = 0

        df = self.calculate_apy_hold(df)
        df = self.calculate_porfolio_returns(df)
        df = self.calculate_performance(df)
        df = self.calculate_performance_adj(df)
        return df


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
