from scipy import stats
from decimal import Decimal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from .Portfolio import Portfolio


class PortfolioHistory:
    def __init__(self, portfolio):
        self.portfolio = portfolio

    # def add_position(self, date, position):
    #     if date in self.positions_history:
    #         self.positions_history[date].append(position)
    #     else:
    #         self.positions_history[date] = [position]

    def portfolio_stats(self):
        """По всем позициям"""
        dfs = []
        for name, pos in self.portfolio.positions.items():

            pos_vol_to_x = pd.DataFrame([pos.history_to_x], index=[f'volume_to_x_{name}']).T
            dfs.append(pos_vol_to_x)

            pos_vol_to_y = pd.DataFrame([pos.history_to_y], index=[f'volume_to_y_{name}']).T
            dfs.append(pos_vol_to_y)

            # Uniswap history
            if hasattr(pos, 'history_fees_to_x'):
                pos_fees_to_x = pd.DataFrame([pos.history_fees_to_x], index=[f'fees_to_x_{name}']).T
                dfs.append(pos_fees_to_x)

            if hasattr(pos, 'history_fees_to_y'):
                pos_fees_to_y = pd.DataFrame([pos.history_fees_to_y], index=[f'fees_to_y_{name}']).T
                dfs.append(pos_fees_to_y)

            if hasattr(pos, 'history_earned_fees_to_x'):
                pos_fees_earned_to_x = pd.DataFrame([pos.history_earned_fees_to_x], index=[f'fees_earned_to_x_{name}']).T
                dfs.append(pos_fees_earned_to_x)

            if hasattr(pos, 'history_earned_fees_to_y'):
                pos_fees_earned_to_y = pd.DataFrame([pos.history_earned_fees_to_y], index=[f'fees_earned_to_y_{name}']).T
                dfs.append(pos_fees_earned_to_y)

            if hasattr(pos, 'impermanent_loss_to_x'):
                pos_il_to_x = pd.DataFrame([pos.history_il_to_x], index=[f'il_to_x_{name}']).T
                dfs.append(pos_il_to_x)

            if hasattr(pos, 'impermanent_loss_to_y'):
                pos_il_to_y = pd.DataFrame([pos.history_il_to_y], index=[f'il_to_y_{name}']).T
                dfs.append(pos_il_to_y)

            if hasattr(pos, 'history_realized_loss_to_x'):
                pos_rl_to_x = pd.DataFrame([pos.history_realized_loss_to_x], index=[f'realized_loss_to_x_{name}']).T
                dfs.append(pos_rl_to_x)

            if hasattr(pos, 'history_realized_loss_to_y'):
                pos_rl_to_y = pd.DataFrame([pos.history_realized_loss_to_y], index=[f'realized_loss_to_y_{name}']).T
                dfs.append(pos_rl_to_y)

        res = pd.concat(dfs, axis=1)

        volume_to_x_cols = [col for col in res.columns if 'volume_to_x' in col]
        res['total_volume_to_x'] = res[volume_to_x_cols].sum(axis=1)

        volume_to_y_cols = [col for col in res.columns if 'volume_to_y' in col]
        res['total_volume_to_y'] = res[volume_to_y_cols].sum(axis=1)

        fees_to_x = [col for col in res.columns if 'fees_to_x' in col]
        res['total_fees_to_x'] = res[fees_to_x].sum(axis=1)

        fees_to_y = [col for col in res.columns if 'fees_to_y' in col]
        res['total_fees_to_y'] = res[fees_to_y].sum(axis=1)

        earned_fees_to_x_cols = [col for col in res.columns if 'fees_earned_to_x' in col]
        res['total_earned_fees_to_x'] = res[earned_fees_to_x_cols].sum(axis=1)

        earned_fees_to_y_cols = [col for col in res.columns if 'fees_earned_to_y' in col]
        res['total_earned_fees_to_y'] = res[earned_fees_to_y_cols].sum(axis=1)

        il_to_x_cols = [col for col in res.columns if 'il_to_x' in col]
        res['total_il_to_x'] = res[il_to_x_cols].sum(axis=1)

        il_to_y_cols = [col for col in res.columns if 'il_to_y' in col]
        res['total_il_to_y'] = res[il_to_y_cols].sum(axis=1)

        rl_to_x_cols = [col for col in res.columns if 'realized_loss_to_x' in col]
        res['total_rl_to_x'] = res[rl_to_x_cols].sum(axis=1)

        rl_to_y_cols = [col for col in res.columns if 'realized_loss_to_y' in col]
        res['total_rl_to_y'] = res[rl_to_y_cols].sum(axis=1)

        res['portfolio_value_to_y'] = res['total_volume_to_y'] + res['total_fees_to_y']

        def g_mean_adj(df):
            out = stats.gmean(df)
            out = out ** (365 / df.shape[0])
            return out

        def yearly_adj(df):
            out = df.iloc[-1] ** (365 / df.shape[0])
            return out

        res['profit_bicurrency'] = (res['total_volume_to_y'] - res['total_volume_to_y'].shift()).cumsum()
        res['portfolio_performance'] = (res['portfolio_value_to_y'] / res['portfolio_value_to_y'].shift()).cumprod()

        res['portfolio_performance_to_y_to_year'] = res['portfolio_performance'].expanding().apply(yearly_adj)

        # res['performance_to_y'] = 1 + res['total_earned_fees_to_y'] / res['total_volume_to_y']
        # res['performance_to_y_yearly'] = res['performance_to_y'].expanding().apply(yearly_adj)
        # res['performance_to_y_year_gmean'] = res['performance_to_y'].expanding().apply(g_mean_adj)
        #
        # res['performance_to_x'] = 1 + res['total_earned_fees_to_x'] / res['total_volume_to_x']
        # res['performance_to_x_yearly'] = res['performance_to_x'].expanding().apply(yearly_adj)
        # res['performance_to_x_year_gmean'] = res['performance_to_x'].expanding().apply(g_mean_adj)
        #
        # res['performance_to_x'] -= 1
        # res['performance_to_y'] -= 1
        # res['performance_to_x_year_gmean'] -= 1
        # res['performance_to_y_year_gmean'] -= 1
        #
        # res['performance_to_y_yearly'] -= 1
        # res['performance_to_x_yearly'] -= 1

        res['portfolio_performance_to_y_to_year'] -= 1
        return res

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

    def draw_portfolio(self):
        portfolio_df = self.portfolio_stats()
        fig1 = self.draw_portfolio_to_x(portfolio_df)
        fig2 = self.draw_portfolio_to_y(portfolio_df)
        # fig3 = self.draw_performance_x(portfolio_df)
        fig4 = self.draw_performance_y(portfolio_df)

        return fig1, fig2, fig4

    def draw_portfolio_to_x(self, portfolio_df):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_volume_to_x'] + portfolio_df['total_fees_to_x'],
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
                y=portfolio_df['total_il_to_x'],
                name="IL to X",
                yaxis="y2"
            ),
             secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Volume to X", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to X', secondary_y=True)
        fig.update_layout(title='Volume and Fees to X')
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
                y=portfolio_df['total_rl_to_y'],
                name="IL to Y",
                yaxis="y2"
            ),
             secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Volume to Y", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to Y', secondary_y=True)
        fig.update_layout(title='Volume and Fees Y')
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

        # fig.add_trace(
        #     go.Scatter(
        #         x=portfolio_df.index,
        #         y=portfolio_df['performance_to_y_year_gmean'],
        #         name="Performance gmean yearly to Y",
        #         yaxis="y2"
        #     ),
        #     secondary_y=True
        # )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Volume to Y", secondary_y=False)
        fig.update_yaxes(title_text='Performance to Y', secondary_y=True)
        fig.update_layout(title='Volume and Performance Y')
        return fig

    # def draw_performance_x(self, portfolio_df):
    #     fig = make_subplots(specs=[[{"secondary_y": True}]])
    #
    #     fig.add_trace(
    #         go.Scatter(
    #             x=portfolio_df.index,
    #             y=portfolio_df['total_volume_to_x'] + portfolio_df['total_fees_to_x'],
    #             name="Volume to X",
    #         ),
    #         secondary_y=False)
    #
    #     fig.add_trace(
    #         go.Scatter(
    #             x=portfolio_df.index,
    #             y=portfolio_df['performance_to_x_yearly'],
    #             name="Performance yearly to X",
    #             yaxis="y2"
    #         ),
    #         secondary_y=True
    #     )
    #
    #     fig.add_trace(
    #         go.Scatter(
    #             x=portfolio_df.index,
    #             y=portfolio_df['performance_to_x_year_gmean'],
    #             name="Performance gmean yearly to X",
    #             yaxis="y2"
    #         ),
    #         secondary_y=True
    #     )
    #
    #     fig.update_xaxes(title_text="Timeline")
    #     fig.update_yaxes(title_text="Volume to X", secondary_y=False)
    #     fig.update_yaxes(title_text='Performance to X', secondary_y=True)
    #     fig.update_layout(title='Volume and Performance X')
    #     return fig

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
