import pandas as pd
import numpy as np


class PortfolioHistory:
    """
       ``PortfolioHistory`` tracks position stats over time.
       Each time ``add_snapshot`` method is called it remembers current state in time.
       All tracked values then can be accessed via ``to_df`` method that will return a ``pandas`` Dataframe.
    """
    def __init__(self):
        self.snapshots = []

    def add_snapshot(self, snapshot: dict):
        """
        Add portfolio snapshot to history
        :param snapshot: dict of portfolio params
        """
        if snapshot:
            self.snapshots.append(snapshot)
        return None

    def to_df(self):
        """
        Transform list of portfolio snapshots to data frame
        :return: Portfolio history data frame
        """
        df = pd.DataFrame(self.snapshots)
        df = df.set_index('timestamp')
        return df

    def calculate_value(self, df):
        """
        Calculate total value of portfolio denomitated in X and Y. Add new columns to historical df
        :return: Portfolio history data frame
        """
        value_to_x_cols = [col for col in df.columns if 'value_to_x' in col]
        value_to_y_cols = [col for col in df.columns if 'value_to_y' in col]

        df[value_to_x_cols] = df[value_to_x_cols].fillna(0)
        df[value_to_y_cols] = df[value_to_y_cols].fillna(0)

        df['total_value_to_x'] = df[value_to_x_cols].sum(axis=1)
        df['total_value_to_y'] = df[value_to_y_cols].sum(axis=1)
        return df

    def calculate_il(self, df):
        """
        Calculate IL of portfolio denomitated in X and Y. Add new columns to historical df
        :return: Portfolio history data frame
        """
        il_to_x_cols = [col for col in df.columns if 'il_to_x' in col]
        il_to_y_cols = [col for col in df.columns if 'il_to_y' in col]
        if il_to_x_cols:
            df[il_to_x_cols] = df[il_to_x_cols].ffill()
            df[il_to_y_cols] = df[il_to_y_cols].ffill()

            df[il_to_x_cols] = df[il_to_x_cols].fillna(0)
            df[il_to_y_cols] = df[il_to_y_cols].fillna(0)

            df['total_il_to_x'] = df[il_to_x_cols].sum(axis=1)
            df['total_il_to_y'] = df[il_to_y_cols].sum(axis=1)
        else:
            df['total_il_to_x'] = 0
            df['total_il_to_y'] = 0
        return df

    def calculate_costs(self, df):
        """
        Costs of portfolio management denomitated in X and Y. Add new columns to historical df
        :return: Portfolio history data frame
        """
        costs_to_x_cols = [col for col in df.columns if 'rebalance_costs_to_x' in col]
        costs_to_y_cols = [col for col in df.columns if 'rebalance_costs_to_y' in col]
        if costs_to_x_cols:
            df[costs_to_x_cols] = df[costs_to_x_cols].ffill()
            df[costs_to_y_cols] = df[costs_to_y_cols].ffill()

            df[costs_to_x_cols] = df[costs_to_x_cols].fillna(0)
            df[costs_to_y_cols] = df[costs_to_y_cols].fillna(0)

            df['total_costs_to_x'] = df[costs_to_x_cols].sum(axis=1)
            df['total_costs_to_y'] = df[costs_to_y_cols].sum(axis=1)
        else:
            df['total_costs_to_x'] = 0
            df['total_costs_to_y'] = 0
        return df

    # def calculate_rl(self, df):
    #     rl_to_x_cols = [col for col in df.columns if 'realized_loss_to_x' in col]
    #     rl_to_y_cols = [col for col in df.columns if 'realized_loss_to_y' in col]
    #
    #     if rl_to_x_cols:
    #         df[rl_to_x_cols] = df[rl_to_x_cols].ffill()
    #         df[rl_to_y_cols] = df[rl_to_y_cols].ffill()
    #
    #         df[rl_to_x_cols] = df[rl_to_x_cols].fillna(0)
    #         df[rl_to_y_cols] = df[rl_to_y_cols].fillna(0)
    #
    #         df['total_rl_to_x'] = df[rl_to_x_cols].sum(axis=1)
    #         df['total_rl_to_y'] = df[rl_to_y_cols].sum(axis=1)
    #     else:
    #         df['total_rl_to_x'] = 0
    #         df['total_rl_to_y'] = 0
    #     return df

    def calculate_actual_fees(self, df):
        """
        Calculate actual fees of Uniswap positions denomitated in X and Y. Add new columns to historical df
        :return: Portfolio history data frame
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

    def calculate_earned_fees(self, df):
        """
        Calculate total erned fees of Uniswap positions denomitated in X and Y. Add new columns to historical df
        :return: Portfolio history data frame
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

    def calculate_performance(self, stats_df):
        """
        Calculate porfolio performance. Add new columns to historical df
        :return: Portfolio history data frame
        """
        def yearly_adj(df):
            days_gone = (df.index[-1] - df.index[0]).days + 1
            out = df.iloc[-1] ** (365 / days_gone)
            return out

        stats_df['profit_bicurrency_to_x'] = (stats_df['total_value_to_x'] - stats_df['total_value_to_x'].shift()).cumsum()
        stats_df['profit_bicurrency_to_y'] = (stats_df['total_value_to_y'] - stats_df['total_value_to_y'].shift()).cumsum()

        stats_df['portfolio_performance_to_x'] = (stats_df['portfolio_value_to_x'] / stats_df['portfolio_value_to_x'].shift()).cumprod()
        stats_df['portfolio_performance_to_y'] = (stats_df['portfolio_value_to_y'] / stats_df['portfolio_value_to_y'].shift()).cumprod()

        stats_df['portfolio_performance_to_x_to_year'] = stats_df['portfolio_performance_to_x'].expanding().apply(yearly_adj)
        stats_df['portfolio_performance_to_y_to_year'] = stats_df['portfolio_performance_to_y'].expanding().apply(yearly_adj)

        stats_df['portfolio_performance_to_x'] -= 1
        stats_df['portfolio_performance_to_x_to_year'] -= 1

        stats_df['portfolio_performance_to_y'] -= 1
        stats_df['portfolio_performance_to_y_to_year'] -= 1
        return stats_df

    def portfolio_stats(self):
        """
        Evalute statistics calculation for portfolio.
        :return: Portfolio history data frame
        """
        df = self.to_df()
        df = self.calculate_value(df)
        df = self.calculate_il(df)
        # df = self.calculate_rl(df)
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

        df = self.calculate_performance(df)
        return df


class RebalanceHistory:
    """
       ``RebalanceHistory`` tracks rebalances over time.
       Each time ``add_snapshot`` method is called it remembers rebalance.
       All tracked values then can be accessed via ``to_df`` method that will return a ``pandas`` Dataframe.
    """
    def __init__(self):
        self.rebalances = {}

    def add_snapshot(self, timestamp, snapshot):
        """
        Add portfolio rebalance snapshot to history
        :param timestamp: timestamp of snapshot
        :param snapshot: dict of portfolio rebalances
        """
        self.rebalances[timestamp] = snapshot
        return None

    def to_df(self):
        """
        Transform list of portfolio rebalance snapshots to data frame
        :return: Portfolio rebalance history data frame
        """
        df = pd.DataFrame([self.rebalances], index=['rebalanced']).T
        df.index.name = 'timestamp'
        return df


class UniPositionsHistory:
    """
       ``UniPositionsHistory`` tracks Uniswap positions over time.
       Each time ``add_snapshot`` method is called it remembers all uniswap positions at current time.
       All tracked values then can be accessed via ``to_df`` method that will return a ``pandas`` Dataframe.
    """
    def __init__(self):
        self.positions = {}

    def add_snapshot(self, timestamp, positions):
        """
        Add uniswap position snapshot to history
        :param timestamp: timestamp of snapshot
        :param positions: list of Uniswap positions
        """       
        uni_positions = {}
        for name, position in positions.items():
            if 'Uni' in name:
                uni_positions[(name, 'lower_bound')] = position.lower_price
                uni_positions[(name, 'upper_bound')] = position.upper_price
        if uni_positions:
            self.positions[timestamp] = uni_positions
        return None

    def to_df(self):
        """
        Transform list of uniswap positions snapshots to data frame
        :return: Uniswap positions history data frame
        """
        intervals_df = pd.DataFrame(self.positions).T
        intervals_df.columns = pd.MultiIndex.from_tuples(intervals_df.columns, names=["pos_name", "bound_type"])
        intervals_df.index.name = 'date'
        return intervals_df

    def get_coverage(self, swaps_df):
        """
        Get coverage metric for all uniswap positions in historic portfolio
        :param swaps_df: UniswapV3 exchange data
        :return: Uniswap positions history data frame
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
