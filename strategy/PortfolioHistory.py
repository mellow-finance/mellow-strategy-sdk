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

    def calculate_position_values(self, positions):
        dfs = []
        for name, pos in positions.items():
            pos_val_to_x = pd.DataFrame([pos.history_to_x], index=[f'value_to_x_{name}']).T
            dfs.append(pos_val_to_x)

            pos_val_to_y = pd.DataFrame([pos.history_to_y], index=[f'value_to_y_{name}']).T
            dfs.append(pos_val_to_y)
        if dfs:
            res_values = pd.concat(dfs, axis=1)
            res_values = res_values.fillna(0)

            val_to_x_cols = [col for col in res_values.columns if 'value_to_x_' in col]
            res_values['total_value_to_x'] = res_values[val_to_x_cols].sum(axis=1)

            val_to_y_cols = [col for col in res_values.columns if 'value_to_y_' in col]
            res_values['total_value_to_y'] = res_values[val_to_y_cols].sum(axis=1)
            return res_values
        else:
            return None

    def calculate_il(self, positions):
        dfs = []
        for name, pos in positions.items():
            if hasattr(pos, 'impermanent_loss_to_x'):
                pos_il_to_x = pd.DataFrame([pos.history_il_to_x], index=[f'il_to_x_{name}']).T
                dfs.append(pos_il_to_x)

            if hasattr(pos, 'impermanent_loss_to_y'):
                pos_il_to_y = pd.DataFrame([pos.history_il_to_y], index=[f'il_to_y_{name}']).T
                dfs.append(pos_il_to_y)
        if dfs:
            res_il = pd.concat(dfs, axis=1)
            res_il = res_il.fillna(0)

            il_to_x_cols = [col for col in res_il.columns if 'il_to_x' in col]
            res_il['total_il_to_x'] = res_il[il_to_x_cols].sum(axis=1)

            il_to_y_cols = [col for col in res_il.columns if 'il_to_y' in col]
            res_il['total_il_to_y'] = res_il[il_to_y_cols].sum(axis=1)
            return res_il
        else:
            return None

    def calculate_rl(self, positions):
        dfs = []
        for name, pos in positions.items():
            if hasattr(pos, 'history_realized_loss_to_x'):
                pos_rl_to_x = pd.DataFrame([pos.history_realized_loss_to_x], index=[f'realized_loss_to_x_{name}']).T
                dfs.append(pos_rl_to_x)

            if hasattr(pos, 'history_realized_loss_to_y'):
                pos_rl_to_y = pd.DataFrame([pos.history_realized_loss_to_y], index=[f'realized_loss_to_y_{name}']).T
                dfs.append(pos_rl_to_y)

        if dfs:
            res_rl = pd.concat(dfs, axis=1)
            res_rl = res_rl.ffill()

            rl_to_x_cols = [col for col in res_rl.columns if 'realized_loss_to_x' in col]
            res_rl['total_rl_to_x'] = res_rl[rl_to_x_cols].sum(axis=1)

            rl_to_y_cols = [col for col in res_rl.columns if 'realized_loss_to_y' in col]
            res_rl['total_rl_to_y'] = res_rl[rl_to_y_cols].sum(axis=1)
            return res_rl
        else:
            return None

    def calculate_actual_fees(self, positions):
        dfs = []
        for name, pos in positions.items():
            if hasattr(pos, 'history_fees_to_x'):
                pos_fees_to_x = pd.DataFrame([pos.history_fees_to_x], index=[f'fees_to_x_{name}']).T
                dfs.append(pos_fees_to_x)

            if hasattr(pos, 'history_fees_to_y'):
                pos_fees_to_y = pd.DataFrame([pos.history_fees_to_y], index=[f'fees_to_y_{name}']).T
                dfs.append(pos_fees_to_y)
        if dfs:
            res_fees = pd.concat(dfs, axis=1)
            res_fees = res_fees.fillna(0)

            fees_to_x = [col for col in res_fees.columns if 'fees_to_x' in col]
            res_fees['total_fees_to_x'] = res_fees[fees_to_x].sum(axis=1)

            fees_to_y = [col for col in res_fees.columns if 'fees_to_y' in col]
            res_fees['total_fees_to_y'] = res_fees[fees_to_y].sum(axis=1)
            return res_fees
        else:
            return None

    def calculate_earned_fees(self, positions):
        dfs = []
        for name, pos in positions.items():
            if hasattr(pos, 'history_earned_fees_to_x'):
                pos_fees_earned_to_x = pd.DataFrame([pos.history_earned_fees_to_x], index=[f'fees_earned_to_x_{name}']).T
                dfs.append(pos_fees_earned_to_x)

            if hasattr(pos, 'history_earned_fees_to_y'):
                pos_fees_earned_to_y = pd.DataFrame([pos.history_earned_fees_to_y], index=[f'fees_earned_to_y_{name}']).T
                dfs.append(pos_fees_earned_to_y)

        if dfs:
            res_fees = pd.concat(dfs, axis=1)
            res_fees = res_fees.ffill()

            earned_fees_to_x_cols = [col for col in res_fees.columns if 'fees_earned_to_x' in col]
            res_fees['total_earned_fees_to_x'] = res_fees[earned_fees_to_x_cols].sum(axis=1)

            earned_fees_to_y_cols = [col for col in res_fees.columns if 'fees_earned_to_y' in col]
            res_fees['total_earned_fees_to_y'] = res_fees[earned_fees_to_y_cols].sum(axis=1)
            return res_fees
        else:
            return None

    def calculate_performance(self, stats_df):
        def yearly_adj(df):
            out = df.iloc[-1] ** (365 / df.shape[0])
            return out
        stats_df['profit_bicurrency_to_y'] = (stats_df['total_value_to_y'] - stats_df['total_value_to_y'].shift()).cumsum()

        stats_df['portfolio_performance_to_x'] = (stats_df['portfolio_value_to_x'] / stats_df['portfolio_value_to_x'].shift()).cumprod()
        stats_df['portfolio_performance_to_y'] = (stats_df['portfolio_value_to_y'] / stats_df['portfolio_value_to_y'].shift()).cumprod()

        stats_df['portfolio_performance_to_x_to_year'] = stats_df['portfolio_performance_to_x'].expanding().apply(yearly_adj)
        stats_df['portfolio_performance_to_y_to_year'] = stats_df['portfolio_performance_to_y'].expanding().apply(yearly_adj)

        stats_df['portfolio_performance_to_x_to_year'] -= 1
        stats_df['portfolio_performance_to_y_to_year'] -= 1
        return stats_df

    def portfolio_stats(self):
        active_positions = self.portfolio.positions
        closed_positions = self.portfolio.positions_closed
        possitions = {**active_positions, **closed_positions}

        values = self.calculate_position_values(possitions)
        il = self.calculate_il(possitions)
        rl = self.calculate_rl(possitions)
        fees = self.calculate_actual_fees(possitions)
        fees_collected = self.calculate_earned_fees(possitions)

        res = pd.concat([values, il, rl, fees, fees_collected], axis=1)

        if 'total_fees_to_x' in res.columns:
            res['portfolio_value_to_x'] = res['total_value_to_x'] + res['total_fees_to_x']
            res['portfolio_value_to_y'] = res['total_value_to_y'] + res['total_fees_to_y']
        else:
            res['portfolio_value_to_x'] = res['total_value_to_x']
            res['portfolio_value_to_y'] = res['total_value_to_y']

        if 'total_il_to_x' in res.columns:
            if 'total_rl_to_x' in res.columns:
                res['total_loss_to_x'] = res['total_il_to_x'] + res['total_rl_to_x']
                res['total_loss_to_y'] = res['total_il_to_y'] + res['total_rl_to_y']
            else:
                res['total_loss_to_x'] = res['total_il_to_x']
                res['total_loss_to_y'] = res['total_il_to_y']
        else:
            res['total_loss_to_x'] = 0
            res['total_loss_to_y'] = 0

        if 'total_earned_fees_to_x' not in res.columns:
            res['total_earned_fees_to_x'] = 0
            res['total_earned_fees_to_y'] = 0

        res = self.calculate_performance(res)
        return res

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
