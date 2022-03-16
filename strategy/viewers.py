import pandas as pd
import polars as pl
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from strategy.history import PortfolioHistory, UniPositionsHistory, RebalanceHistory
from strategy.data import PoolDataUniV3
from strategy.primitives import Pool


class PotrfolioViewer:
    """
    ``PotrfolioViewer`` is class for backtest result visualisation.

    Attributes:
        portfolio_history:
            ``PortfolioHistory`` instance returned from backtest
        pool:
            ``Pool``
    """
    def __init__(self, portfolio_history: PortfolioHistory, pool: Pool, offset: int = 30):
        self.portfolio_history = portfolio_history
        self.pool = pool
        self.offset = offset

    def draw_portfolio(self):
        """
        Main function of the class. Create main plots to track portfolio behavior.

        Returns: plotly plots
            | fig1: portfolio value in X, fees in X, IL in X
            | fig2: portfolio value in Y, fees in Y, IL in Y
            | fig3: portfolio value in X, portfolio APY in X
            | fig4: portfolio value in Y, portfolio APY in Y
            | fig5: amount of X asset in portfolio,  amount of Y asset in portfolio
            | fig6: V@p_n in X, APY(V@p_n)
        """
        portfolio_df = self.portfolio_history.calculate_stats()
        delta = datetime.timedelta(days=self.offset)
        start_date = portfolio_df['timestamp'][0] + delta
        portfolio_df_offset = portfolio_df.filter(pl.col('timestamp') >= start_date)

        fig1 = self.draw_portfolio_to_x(portfolio_df_offset)
        fig2 = self.draw_portfolio_to_y(portfolio_df_offset)
        fig3 = self.draw_performance_x(portfolio_df_offset)
        fig4 = self.draw_performance_y(portfolio_df_offset)
        fig5 = self.draw_x_y(portfolio_df_offset)
        fig6 = self.draw_vpn_vs_hold_apy(portfolio_df_offset)
        return fig1, fig2, fig3, fig4, fig5, fig6

    def draw_portfolio_to_x(self, portfolio_df: pl.DataFrame):
        """
        Plot portfolio value in X, fees in X, IL in X.
        Args:
            portfolio_df:
                result of ``PortfolioHistory.calculate_stats()``
        Returns:
            plotly plot
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_value_to_x'],
                name=f"Portfolio value in {self.pool.token0.name}",
            ), secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_fees_to_x'],
                name=f'Earned fees in {self.pool.token0.name}',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_il_to_x'],
                name=f"IL in {self.pool.token0.name}",
                yaxis="y2"
            ), secondary_y=True)

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to X", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to X', secondary_y=True)
        fig.update_layout(title=f'Portfolio Value, Fees and IL in {self.pool.token0.name}', width=900, height=500)
        return fig

    def draw_portfolio_to_y(self, portfolio_df: pd.DataFrame):
        """
        Plot portfolio value and fees in Y.

        Args:
            portfolio_df:
                result of ``PortfolioHistory.calculate_stats()``

        Returns:
            plotly plot
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_value_to_y'],
                name=f"Portfolio value in {self.pool.token1.name}",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_fees_to_y'],
                name=f'Earned fees in {self.pool.token1.name}',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_il_to_y'],
                name=f"IL in {self.pool.token1.name}",
                yaxis="y2"
            ),  secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to Y", secondary_y=False)
        fig.update_yaxes(title_text='Earned fees to Y', secondary_y=True)
        fig.update_layout(title=f'Portfolio Value, Fees and IL in {self.pool.token1.name}', width=900, height=500)
        return fig

    def draw_performance_x(self, portfolio_df: pd.DataFrame):
        """
        Plot portfolio value in X, portfolio APY in X.

        Args:
            portfolio_df:
                result of ``PortfolioHistory.calculate_stats()``

        Returns:
            plotly plot
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_value_to_x'],
                name=f"Portfolio value in {self.pool.token0.name}",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['portfolio_apy_x'],
                name=f"APY in {self.pool.token0.name}",
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
        Plot portfolio value in Y, portfolio APY in Y.

        Args:
            portfolio_df:
                result of ``PortfolioHistory.calculate_stats()``
        Returns:
            plotly plot
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_value_to_y'],
                name=f"Portfolio value in {self.pool.token1.name}",
            ), secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['portfolio_apy_y'],
                name=f"APY in {self.pool.token1.name}",
                yaxis="y2"
            ), secondary_y=True)

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value to Y", secondary_y=False)
        fig.update_yaxes(title_text=f'APY in {self.pool.token1.name}', secondary_y=True)

        fig.update_layout(title=f'Portfolio Value and APY in {self.pool.token1.name}')
        return fig

    def draw_x_y(self, portfolio_df: pd.DataFrame):
        """
        | Plot amount of X asset in portfolio
        | Plot amount of Y asset in portfolio

        Args:
            portfolio_df:
                result of ``PortfolioHistory.calculate_stats()``
        Returns:
            plotly plot
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_value_x'],
                name=f"Portfolio value in {self.pool.token0.name}",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['total_value_y'],
                name=f'Portfolio value in {self.pool.token1.name}',
                yaxis='y2',

            ), secondary_y=True)

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Value in X", secondary_y=False)
        fig.update_yaxes(title_text='Value in Y', secondary_y=True)
        fig.update_layout(title=f'Portfolio Value in {self.pool.token0.name}, {self.pool.token1.name}')
        return fig

    def draw_vpn_vs_hold_apy(self, portfolio_df: pd.DataFrame):
        """
        | Plot portfolio value in X in condition of price=last price (in code Vpn or V@p_n).
        | Plot APY of V@p_n. (btw APY(V@p_n in X) equals APY(V@p_n in Y))

        Args:
            portfolio_df: result of ``PortfolioHistory.calculate_stats()``
        Returns:
            plotly plot
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['vpn_apy'],
                name=f"Portfolio V@p_n APY",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df['timestamp'].to_list(),
                y=portfolio_df['vpn_value'],
                name=f'Portfolio V@p_n in X',
            ),
            secondary_y=True)

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="APY", secondary_y=False)
        fig.update_yaxes(title_text='Value', secondary_y=True)
        fig.update_layout(title=f'Portfolio Value in {self.pool.token1.name}, Portfolio Value and APY at price_n')
        return fig


class UniswapViewer:
    # TODO docs
    """
     ``UniswapViewer`` is class for visualizing UniswapV3 intervals in time.

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
        intervals_df = self.uni_postition_history.to_df()
        positions = intervals_df['name'].unique().to_list()
        positions_num = len(positions) - 1

        fig = go.Figure()
        for i, name in enumerate(positions):
            pos = intervals_df.filter(pl.col('name') == name)

            batch = [go.Scatter(
                name='Lower Bound',
                x=pos['timestamp'].to_list(),
                y=pos['upper_bound'].to_list(),
                mode='lines',
                marker=dict(color='blue'),
                line=dict(width=1),
                legendgroup='Interval',
                showlegend=(False if i != positions_num else True)
            ),
                go.Scatter(
                    name='Upper Bound',
                    x=pos['timestamp'].to_list(),
                    y=pos['lower_bound'].to_list(),
                    marker=dict(color='blue'),
                    line=dict(width=1),
                    mode='lines',
                    fillcolor='rgba(0, 0, 200, 0.1)',
                    fill='tonexty',
                    legendgroup='Interval',
                    showlegend=(False if i != positions_num else True)
                )]
            fig.add_traces(batch)

        fig.add_trace(go.Scatter(
            name='Price',
            x=swaps_df['timestamp'].to_list(),
            y=swaps_df['price'].to_list(),
            mode='lines',
            line=dict(color='rgb(0, 200, 0)'),
        ))
        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Price")
        fig.update_layout(title='UniV3 positions', width=900, height=400)
        return fig


class RebalanceViewer:
    # TODO docs
    """
    ``RebalanceViewer`` class for visualizing rebalances that occurred during the back test.

    Attributes:
        rebalance_history:
            ``RebalanceHistory`` instance returned from backtest.
    """
    def __init__(self, rebalance_history: RebalanceHistory):
        self.rebalance_history = rebalance_history

    def draw_rebalances(self, swaps_df: pd.DataFrame):
        """
        Plot portfolio rabalances.

        Args:
            swaps_df: price data. (timestamp, price).

        Returns: Plot with portfolio rabalances
        """
        rebalance_df = self.rebalance_history.to_df()
        swaps_df_slice = swaps_df[['timestamp', 'price']].join(rebalance_df, on='timestamp')

        fig = go.Figure()
        fig.add_trace(
                    go.Scatter(
                        x=swaps_df['timestamp'].to_list(),
                        y=swaps_df['price'],
                        name="Price",
                        )
                    )

        events = rebalance_df['rebalance'].unique()
        for event in events:
            rebalance_df_slice = swaps_df_slice.filter(pl.col('rebalance') == event)

            fig.add_trace(
                        go.Scatter(
                            x=rebalance_df_slice['timestamp'].to_list(),
                            y=rebalance_df_slice['price'],
                            mode='markers',
                            # marker_color='red',
                            marker_size=7,
                            marker_symbol='circle-open',
                            marker_line_width=2,
                            name=f"{event}",
                            )
                        )
        fig.update_xaxes(title_text="Timeline")
        fig.update_layout(title='Rebalances')
        return fig


class LiquidityViewer:
    """
    ``LiquidityViewer`` is class for liquidity visualisation.
    """
    def __init__(self, pool_data: PoolDataUniV3):
        self.pool = pool_data

    def draw_plot(self):
        """
        Plot liquidity and price in pool in time.

        Returns:
            Plot with Pool liquidity and price.
        """
        spot_prices = self.pool.swaps.groupby('date').agg([
            pl.col('price').mean().alias('price')
        ]).sort(by='date')

        daily_mints = self.pool.mints.groupby('date').agg([
            pl.col('liquidity').sum().alias('mint')
        ]).sort(by='date')

        daily_burns = self.pool.burns.groupby('date').agg([
            pl.col('liquidity').sum().alias('burn')
        ]).sort(by='date')

        df1 = daily_mints.join(daily_burns, on=['date'], how='outer').fill_null(0)
        df2 = spot_prices.join(df1, on=['date'], how='outer').fill_null(0)
        df3 = df2.with_column(
            (pl.col('mint') - pl.col('burn')).cumsum().alias('liq')
        )

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=df3['date'].to_list(),
                y=df3['price'].to_list(),
                name="Price",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=df3['date'].to_list(),
                y=df3['liq'].to_list(),
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
