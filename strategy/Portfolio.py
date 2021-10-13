from .Positions import AbstractPosition
from typing import List
from datetime import datetime

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
        return None

