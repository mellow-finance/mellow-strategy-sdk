from .Positions import AbstractPosition
from typing import List
from datetime import datetime
import copy


class Portfolio(AbstractPosition):
    def __init__(self,
                 name: str,
                 positions: List[AbstractPosition] = None):
        super().__init__(name)
        if positions is None:
            positions = []
        self.positions = {pos.name: pos for pos in positions}
        self.positions_closed = {}

        self.portfolio_history = {}

    def append(self, position: AbstractPosition) -> None:
        self.positions[position.name] = position
        return None

    def remove(self, name: str) -> None:
        if name not in self.positions:
            raise Exception(f'Invalid name = {name}')
        self.positions_closed[name] = copy.copy(self.positions[name])
        del self.positions[name]
        return None

    def get_position(self, name: str) -> AbstractPosition:
        if name not in self.positions:
            raise Exception(f'Invalid name = {name}')
        return self.positions[name]

    def get_last_position(self) -> AbstractPosition:
        if self.positions:
            last_key = list(self.positions.keys())[-1]
            pos = self.get_position(last_key)
            return pos
        else:
            raise Exception(f'Position not found')

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

