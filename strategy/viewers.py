import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from strategy.history import PortfolioHistory, UniPositionsHistory, RebalanceHistory
from strategy.data import PoolDataUniV3
from strategy.primitives import Pool


class PotrfolioViewer:
    """
    PotrfolioViewer is class for potrfolio visualisation.

    Attributes:
        portfolio_history: Portfolio history instance.
        pool: UniV3 pool meta information.
    """
    def __init__(self, portfolio_history: PortfolioHistory, pool: Pool):
        self.portfolio_history = portfolio_history
        self.pool = pool

    def draw_portfolio(self):
        """
        Plot in pool in time.

        Returns:
            Portfolio visualization.
        """
        portfolio_df = self.portfolio_history.portfolio_stats()
        fig1 = self.draw_portfolio_to_x(portfolio_df)
        fig2 = self.draw_portfolio_to_y(portfolio_df)
        fig3 = self.draw_performance_x(portfolio_df)
        fig4 = self.draw_performance_y(portfolio_df)
        return fig1, fig2, fig3, fig4

    def draw_portfolio_to_x(self, portfolio_df: pd.DataFrame):
        """
        Plot portfolio value and fees in X.

        Args:
            portfolio_df: Portfolio history data frame.

        Returns:
            Portfolio plot with value, fees, il.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_x'],
                name=f"Portfolio value in {self.pool.token0.name}",
            ), secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_earned_fees_to_x'],
                name=f'Earned fees in {self.pool.token0.name}',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_loss_to_x'],
                name=f"IL in {self.pool.token0.name}",
                yaxis="y2"
            ), secondary_y=True)

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to X", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to X', secondary_y=True)
        fig.update_layout(title=f'Portfolio Value, Fees and IL in {self.pool.token0.name}')
        return fig

    def draw_portfolio_to_y(self, portfolio_df: pd.DataFrame):
        """
        Plot portfolio value and fees in Y.

        Args:
            portfolio_df: Portfolio history data frame.

        Returns:
            Portfolio plot with value, fees, il.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_y'],
                name=f"Portfolio value in {self.pool.token1.name}",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_earned_fees_to_y'],
                name=f'Earned fees in {self.pool.token1.name}',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_loss_to_y'],
                name=f"IL in {self.pool.token1.name}",
                yaxis="y2"
            ),  secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to Y", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to Y', secondary_y=True)
        fig.update_layout(title=f'Portfolio Value, Fees and IL in {self.pool.token1.name}')
        return fig

    def draw_performance_x(self, portfolio_df: pd.DataFrame):
        """
        Plot portfolio performance in X.

        Args:
            portfolio_df: portfolio history data frame

        Returns:
            Portfolio plot with value and apy.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_x'],
                name=f"Portfolio value in {self.pool.token0.name}",
            ),
            secondary_y=False)
        
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_to_x_apy'],
                name=f"APY in {self.pool.token0.name}",
                yaxis="y2"
            ),
            secondary_y=True
        )
        
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_rel_to_x_apy'],
                name=f"APY relative to bicurrency in {self.pool.token0.name}",
                yaxis="y2"
            ),
            secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to X", secondary_y=False)
        fig.update_yaxes(title_text=f'APY in {self.pool.token0.name}', secondary_y=True)

        fig.update_layout(title=f'Portfolio Value and APY in {self.pool.token0.name}')
        return fig
    
    def draw_performance_y(self, portfolio_df: pd.DataFrame):
        """
        Plot portfolio performance in Y.

        Args:
            portfolio_df: Portfolio history data frame.

        Returns:
            Portfolio plot with value and apy.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_value_to_y'],
                name=f"Portfolio value in {self.pool.token1.name}",
            ), secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_to_y_apy'],
                name=f"APY in {self.pool.token1.name}",
                yaxis="y2"
            ), secondary_y=True)
        
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['portfolio_performance_rel_to_y_apy'],
                name=f"APY relative to bicurrency in {self.pool.token1.name}",
                yaxis="y2"
            ), secondary_y=True)

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to Y", secondary_y=False)
        fig.update_yaxes(title_text=f'APY in {self.pool.token1.name}', secondary_y=True)

        fig.update_layout(title=f'Portfolio Value and APY in {self.pool.token1.name}')
        return fig
    
    def draw_liquidity(self, portfolio_df):
        """
        Plot portfolio liquidity in UniswapV3.

        Args:
            portfolio_df: Portfolio history data frame.

        Returns:
            Portfolio plot with liquidity.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['price'],
                name="Price",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_current_liquidity'],
                name="Current liquidity",
                yaxis="y2"
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Price", secondary_y=False)
        fig.update_yaxes(title_text='Liquidity', secondary_y=True)
        fig.update_layout(title='Portfolio Liquidity')
        
        return fig


class UniswapViewer:
    """
     UniswapViewer is class for visualizing UniswapV3 intervals in time.

     Attributes:
        uni_postition_history: Uniswap positions history instance.
    """
    def __init__(self, uni_postition_history: UniPositionsHistory):
        self.uni_postition_history = uni_postition_history

    def draw_intervals(self, swaps_df):
        """
        Plot uniswap positions intervals in time.

        Args:
            swaps_df: UniswapV3 exchange data.

        Returns:
            Plot with UniswapV3 position intervals.
        """
        intervals = self.uni_postition_history.to_df()
        fig = go.Figure()

        for col_0 in intervals.columns.get_level_values(level=0).unique():
            pos = intervals.loc[:, intervals.columns.get_level_values(level=0) == col_0]
            pos_clear = pos.dropna()

            low = pos_clear[(col_0, 'lower_bound')].to_numpy()
            up = pos_clear[(col_0, 'upper_bound')].to_numpy()

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
            x=swaps_df.index,
            y=swaps_df['price'],
            mode='lines',
            line=dict(color='rgb(0, 200, 0)'),
        ))
        fig.update_layout(title='UniV3 positions')
        return fig


class RebalanceViewer:
    """
    RebalanceViewer is class for rebalance visualisation.

    Attributes:
        rebalance_history: Rebalance history instance.
    """
    def __init__(self, rebalance_history: RebalanceHistory):
        self.rebalance_history = rebalance_history

    def draw_rebalances(self, swaps_df: pd.DataFrame):
        """
        Plot portfolio rabalances.

        Args:
            swaps_df: UniswapV3 exchange data.

        Returns: Plot with portfolio rabalances
        """
        rebalance_df = self.rebalance_history.to_df()
        swaps_df_slice = swaps_df.loc[rebalance_df.index]

        rebalance_df = rebalance_df.dropna()

        fig = go.Figure()
        fig.add_trace(
                    go.Scatter(
                        x=swaps_df_slice.index,
                        y=swaps_df_slice['price'],
                        name="Price",
                        )
                    )

        events = rebalance_df['rebalanced'].unique()
        for event in events:
            rebalance_df_slice = swaps_df_slice.loc[rebalance_df.loc[rebalance_df['rebalanced'] == event].index]

            fig.add_trace(
                        go.Scatter(
                            x=rebalance_df_slice.index,
                            y=rebalance_df_slice['price'],
                            mode='markers',
                            # marker_color='red',
                            marker_size=7,
                            marker_symbol='circle-open',
                            marker_line_width=2,
                            name=f"Rebalances {event}",
                            )
                        )
        fig.update_xaxes(title_text="Timeline")
        fig.update_layout(title='Rebalances')
        return fig


class LiquidityViewer:
    """
    LiquidityViewer is class for liquidity visualisation.
    """
    def __init__(self, pool_data: PoolDataUniV3):
        self.pool = pool_data

    def draw_plot(self):
        """
        Plot liquidity in pool in time.

        Returns:
            Plot with Pool liquidity.
        """
        spot_prices = self.pool.swaps[['price']].resample('D').mean()
        daily_mints = self.pool.mints[['amount']].resample('D').sum()
        daily_burns = self.pool.burns[['amount']].resample('D').sum()
        daily_liq = daily_mints - daily_burns
        total_liq = daily_liq.cumsum()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=spot_prices.index,
                y=spot_prices['price'],
                name="Price",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=total_liq.index,
                y=total_liq['amount'],
                name='Liquidity',
                yaxis='y2',

            ), secondary_y=True)
        # Set x-axis title
        fig.update_xaxes(title_text="Timeline")
        # Set y-axes titles
        fig.update_yaxes(title_text="Price", secondary_y=False)
        fig.update_yaxes(title_text='Liquidity', secondary_y=True)
        fig.update_layout(title='Price and Liquidity')
        return fig
