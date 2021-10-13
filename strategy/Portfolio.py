from .Positions import AbstractPosition
from typing import List
from datetime import datetime
import pandas as pd
import copy

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


class Portfolio(AbstractPosition):
    def __init__(self,
                 name: str,
                 positions: List[AbstractPosition] = None):
        super().__init__(name)
        if positions is None:
            positions = []
        self.positions = {pos.name: pos for pos in positions}

        self.portfolio_history = {}

    def append(self, position: AbstractPosition) -> None:
        self.positions[position.name] = position
        return None

    def remove(self, name: str) -> None:
        if name not in self.positions:
            raise Exception(f'Invalid name = {name}')
        del self.positions[name]
        return None

    def get_position(self, name: str) -> AbstractPosition:
        if name not in self.positions:
            raise Exception(f'Invalid name = {name}')
        return self.positions[name]

    def positions_list(self) -> List:
        return list(self.positions.values())

    def to_x(self, price: float):
        total_x = 0
        for name, pos in self.positions.items():
            total_x += pos.to_x(price)
        return total_x

    def to_y(self, price: float):
        total_y = 0
        for name, pos in self.positions.items():
            total_y += pos.to_y(price)
        return total_y

    def to_xy(self, price: float):
        total_x = 0
        total_y = 0
        for name, pos in self.positions.items():
            x, y = pos.to_xy(price)
            total_x += x
            total_y += y
        return total_x, total_y

    def snapshot(self, date: datetime, price: float) -> None:
        for name, pos in self.positions.items():
            pos.snapshot(date, price)
        self.portfolio_history[date] = copy.copy(self.positions)
        return None

    def portfolio_stats(self):
        dfs = []
        for name, pos in self.positions.items():
            pos_vol_y = pd.DataFrame([pos.history_y], index=[f'volume_y_{name}']).T
            dfs.append(pos_vol_y)
            if hasattr(pos, 'history_fees_y'):
                pos_fees_y = pd.DataFrame([pos.history_fees_y], index=[f'fees_y_{name}']).T
                dfs.append(pos_fees_y)

            if hasattr(pos, 'history_il_y'):
                pos_fees_y = pd.DataFrame([pos.history_il_y], index=[f'il_y{name}']).T
                dfs.append(pos_fees_y)

        res = pd.concat(dfs, axis=1)

        volume_cols = [col for col in res.columns if 'volume_y' in col]
        res['total_vol'] = res[volume_cols].sum(axis=1)

        fees_cols = [col for col in res.columns if 'fees_y' in col]
        res['total_fees'] = res[fees_cols].sum(axis=1)

        il_cols = [col for col in res.columns if 'il_y' in col]
        res['total_il'] = res[il_cols].sum(axis=1)

        return res

    def draw_portfolio(self):
        portfolio_df = self.portfolio_stats()
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_vol'],
                name="Volume",
            ),
            secondary_y=False)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_fees'],
                name='Fees',
                yaxis='y2',

            ), secondary_y=True)

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df['total_il'],
                name="IL",
                yaxis="y2"
            ),
             secondary_y=True
        )

        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text="Volume", secondary_y=False)
        fig.update_yaxes(title_text='Fees', secondary_y=True)
        fig.update_layout(title='Volume and Fees')
        return fig

    def uniswap_intervals(self):
        result = []
        for date, positions in self.portfolio_history.items():
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

