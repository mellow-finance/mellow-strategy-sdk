from scipy import stats
from decimal import Decimal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class PortfolioHistory:
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

    def draw_portfolio(self):
        portfolio_df = self.portfolio_stats()
        fig1 = self.draw_portfolio_to_x(portfolio_df)
        fig2 = self.draw_portfolio_to_y(portfolio_df)
        fig3 = self.draw_performance_x(portfolio_df)
        fig4 = self.draw_performance_y(portfolio_df)
        return fig1, fig2, fig3, fig4

    def draw_portfolio_to_x(self, portfolio_df):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_x'],
                name="Volume to X",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_earned_fees_to_x'],
                name='Earned fees to X',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_loss_to_x'],
                name="Loss to X",
                yaxis="y2"
            ),
             secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to X", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to X', secondary_y=True)
        fig.update_layout(title='Portfolio Value, Fees and Loss to X')
        return fig

    def draw_portfolio_to_y(self, portfolio_df):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_y'],
                name="Volume to Y",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_earned_fees_to_y'],
                name='Earned fees to Y',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_loss_to_y'],
                name="Loss to Y",
                yaxis="y2"
            ),
             secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to Y", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to Y', secondary_y=True)
        fig.update_layout(title='Portfolio Value and Fees Y')
        return fig

    def draw_performance_y(self, portfolio_df):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_y'],
                name="Volume to Y",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_to_y_to_year'],
                name="Performance yearly to Y",
                yaxis="y2"
            ),
            secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to Y", secondary_y=False)
        fig.update_yaxes(title_text='Performance to Y', secondary_y=True)

        lower = portfolio_df['portfolio_performance_to_y_to_year'].quantile(0.03)
        upper = portfolio_df['portfolio_performance_to_y_to_year'].quantile(0.97)
        fig.update_yaxes(range=[lower, upper], secondary_y=True)

        fig.update_layout(title='Portfolio Value and Performance Y')
        return fig

    def draw_performance_x(self, portfolio_df):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_x'],
                name="Volume to X",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_to_x_to_year'],
                name="Performance yearly to X",
                yaxis="y2"
            ),
            secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to X", secondary_y=False)
        fig.update_yaxes(title_text='Performance to X', secondary_y=True)

        lower = portfolio_df['portfolio_performance_to_x_to_year'].quantile(0.03)
        upper = portfolio_df['portfolio_performance_to_x_to_year'].quantile(0.97)
        fig.update_yaxes(range=[lower, upper], secondary_y=True)

        fig.update_layout(title='Portfolio Value and Performance X')
        return fig


    def uniswap_intervals(self):
        result = []
        for date, positions in self.portfolio.portfolio_history.items():
            res_df = pd.DataFrame()
            for name, position in positions.items():
                if 'Uni' in name:
                    pos_inttervals = pd.DataFrame(data=[(position.lower_price, position.upper_price)],
                                                  columns=[(position.name, 'min_bound'), (position.name, 'max_bound')],
                                                  index=[date])
                    res_df = pd.concat([res_df, pos_inttervals], axis=1)

            result.append(res_df)

        final = pd.concat(result)
        final.index.name = 'date'
        return final

    def draw_intervals(self, pool_data):
        intervals = self.uniswap_intervals()
        fig = go.Figure()

        for col_0 in intervals.columns.get_level_values(level=0).unique():
            pos = intervals.loc[:, intervals.columns.get_level_values(level=0) == col_0]
            pos_clear = pos.dropna()

            low = pos_clear[(col_0, 'min_bound')].to_numpy()
            up = pos_clear[(col_0, 'max_bound')].to_numpy()

            batch = [go.Scatter(
                name='Upper Bound ' + str(col_0),
                x=pos_clear.index,
                y=up,
                mode='lines',
                marker=dict(color='blue'),
                line=dict(width=1),
                showlegend=False
            ),
                go.Scatter(
                    name='Lower Bound ' + str(col_0),
                    x=pos_clear.index,
                    y=low,
                    marker=dict(color='blue'),
                    line=dict(width=1),
                    mode='lines',
                    fillcolor='rgba(0, 0, 200, 0.1)',
                    fill='tonexty',

                    showlegend=False
                )]
            fig.add_traces(batch)

        fig.add_trace(go.Scatter(
            name='Price',
            x=pool_data.spot_prices.index,
            y=pool_data.spot_prices['price'],
            mode='lines',
            line=dict(color='rgb(0, 200, 0)'),
        ))
        fig.update_layout(title='Intevals')
        return fig
