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
        if snapshot:
            self.snapshots.append(snapshot)
        return None

    def to_df(self):
        df = pd.DataFrame(self.snapshots)
        df = df.set_index('timestamp')
        return df

    def calculate_value(self, df):
        value_to_x_cols = [col for col in df.columns if 'value_to_x' in col]
        value_to_y_cols = [col for col in df.columns if 'value_to_y' in col]

        df[value_to_x_cols] = df[value_to_x_cols].fillna(0)
        df[value_to_y_cols] = df[value_to_y_cols].fillna(0)

        df['total_value_to_x'] = df[value_to_x_cols].sum(axis=1)
        df['total_value_to_y'] = df[value_to_y_cols].sum(axis=1)
        return df

    def calculate_il(self, df):
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
        self.rebalances[timestamp] = snapshot
        return None

    def to_df(self):
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
        uni_positions = {}
        for name, position in positions.items():
            if 'Uni' in name:
                uni_positions[name] = position
        self.positions[timestamp] = uni_positions
        return None

    def to_df(self):
        result = []
        for date, positions in self.positions.items():
            res_df = pd.DataFrame()
            for name, position in positions.items():

                pos_inttervals = pd.DataFrame(data=[(position.lower_price, position.upper_price)],
                                             columns=[(position.name, 'min_bound'), (position.name, 'max_bound')],
                                             index=[date])
                res_df = pd.concat([res_df, pos_inttervals], axis=1)

            result.append(res_df)

        intervals_df = pd.concat(result)
        intervals_df.columns = pd.MultiIndex.from_tuples(intervals_df.columns, names=["pos_name", "bound_type"])
        intervals_df.index.name = 'date'
        return intervals_df

    def get_coverage(self, swaps_df):
        prices = swaps_df[['price']]
        prices['covered'] = np.nan

        intervals = self.to_df()
        for col_0 in intervals.columns.get_level_values(level=0).unique():
            pos = intervals.loc[:, intervals.columns.get_level_values(level=0) == col_0]
            pos_clear = pos.dropna()

            idx = pos_clear.index
            low = pos_clear[(col_0, 'min_bound')]
            up = pos_clear[(col_0, 'max_bound')]

            prices_slice = prices.loc[idx]
            mask = (low <= prices_slice['price']) & (prices_slice['price'] <= up)
            prices.loc[idx, 'covered'] = mask

        prices['covered'] = prices['covered'].fillna(False)
        coverage = prices['covered'] / prices.shape[0]
        return coverage
