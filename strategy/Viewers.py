import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .History import PortfolioHistory, UniPositionsHistory


class PotrfolioViewer:
    def __init__(self, portfolio_history: PortfolioHistory):
        self.portfolio_history = portfolio_history

    def draw_portfolio(self):
        portfolio_df = self.portfolio_history.portfolio_stats()
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
            ), secondary_y=False)

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
            ), secondary_y=True)

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
            ),  secondary_y=True
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
            ), secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_to_y_to_year'],
                name="Performance yearly to Y",
                yaxis="y2"
            ), secondary_y=True)

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


class UniswapViewer:
    def __init__(self, uni_postition_history: UniPositionsHistory):
        self.uni_postition_history = uni_postition_history

    def draw_intervals(self, swaps_df):
        intervals = self.uni_postition_history()
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
            x=swaps_df.spot_prices.index,
            y=swaps_df.spot_prices['price'],
            mode='lines',
            line=dict(color='rgb(0, 200, 0)'),
        ))
        fig.update_layout(title='Intevals')
        return fig
