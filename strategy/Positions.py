from typing import Tuple
from abc import ABC, abstractmethod
import numpy as np


class AbstractPosition(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def to_x(self, price: float) -> float:
        raise Exception(NotImplemented)

    @abstractmethod
    def to_y(self, price: float) -> float:
        raise Exception(NotImplemented)

    @abstractmethod
    def to_xy(self, price: float) -> Tuple[float, float]:
        raise Exception(NotImplemented)


class BicurrencyPosition(AbstractPosition):
    def __init__(self, name: str,
                 swap_fee: float,
                 x: float = None,
                 y: float = None,
                 ) -> None:
        super().__init__(name)
        self.x = 0
        if x is not None:
            self.x = x

        self.y = 0
        if y is not None:
            self.y = y

        self.swap_fee = swap_fee

    def deposit(self, x: float, y: float) -> None:
        self.x += x
        self.y += y
        return None

    def withdraw(self, x: float, y: float) -> Tuple[float, float]:
        self.x -= x
        self.y -= y
        return x, y

    def adjust(self, price: float) -> None:
        '''implement UniswapV3 swaping math: add liqudity dependency on swaping price'''
        dV = price * self.x - self.y
        denom = 2 - self.swap_fee
        if dV > 0:
            dx = dV / (price * denom)
            self.swap_x_to_y(dx, price)

        elif dV < 0:
            dy = abs(dV) / denom
            self.swap_y_to_x(dy, price)

        return None

    def to_x(self, price: float) -> float:
        # price = x/y
        res = self.x + self.y / price
        return res

    def to_y(self, price: float) -> float:
        # price = x/y
        res = self.x * price + self.y
        return res

    def to_xy(self, price: float) -> Tuple[float, float]:
        return self.x, self.y

    def swap_x_to_y(self, dx: float, price: float) -> None:
        '''implement UniswapV3 swaping math: add liqudity dependency on swaping price'''
        self.x -= dx
        self.y += price * (1 - self.swap_fee) * dx
        return None

    def swap_y_to_x(self, dy: float, price: float) -> None:
        '''implement UniswapV3 swaping math: add liqudity dependency on swaping price'''
        self.y -= dy
        self.x += (1 - self.swap_fee) * dy / price
        return None


class UniV3Position(AbstractPosition):
    def __init__(self,
                 name: str,
                 lower_price: float,
                 upper_price: float,
                 fee_percent: float) -> None:

        super().__init__(name)

        self.lower_price = lower_price
        self.upper_price = upper_price
        self.fee_percent = fee_percent

        self.sqrt_lower = np.sqrt(self.lower_price)
        self.sqrt_upper = np.sqrt(self.upper_price)
        self.liquidity = 0
        self.realized_loss = 0
        self.price_init = None

        self.fees_x = 0
        self.fees_y = 0

    def mint(self, x: float, y: float, price: float) -> None:
        self.price_init = price
        x_aligned, y_aligned = self._liqudity_aligning_(x, y, price)
        dliq = self._liq_(x_aligned, y_aligned, price)
        self.liquidity = dliq
        return None

    def burn(self, price: float) -> Tuple[float, float]:
        x_out, y_out = self.to_xy(price)
        self.liquidity = 0
        realized_loss = self.impermanent_loss(price)
        self.realized_loss = realized_loss
        return x_out, y_out

    def collect_fees(self, price_0: float, price_1: float) -> None:
        price_0_adj = self._adj_price_(price_0)
        price_1_adj = self._adj_price_(price_1)

        x_0, y_0 = self.to_xy(price_0_adj)
        x_1, y_1 = self.to_xy(price_1_adj)

        fee_x, fee_y = 0, 0
        if y_0 <= y_1:
            fee_y = (y_0 - y_1) * self.fee_percent
        else:
            fee_x = (x_0 - x_1) * self.fee_percent
        self.fees_x += fee_x
        self.fees_y += fee_y
        return None

    def impermanent_loss(self, price: float) -> float:
        sqrt_price_init = np.sqrt(self.price_init)
        volume_y_held = self.liquidity * (
                    sqrt_price_init - self.sqrt_lower + price * (1 / sqrt_price_init - 1 / self.sqrt_upper))
        il = volume_y_held - self.to_y(price)
        return il

    def to_x(self, price: float) -> float:
        x, y = self.to_xy(price)
        vol_x = x + y / price
        return vol_x

    def to_y(self, price: float) -> float:
        x, y = self.to_xy(price)
        vol_y = x * price + y
        return vol_y

    def to_xy(self, price) -> Tuple[float, float]:
        x, y = self._liq_to_xy_(self.liquidity, price)
        return x, y

    def _adj_price_(self, price: float) -> float:
        adj_price = min(max(self.lower_price, price), self.upper_price)
        return adj_price

    def _liq_x_(self, x: float, price: float) -> float:
        if self.upper_price <= price:
            return np.inf
        sqrt_price = np.sqrt(price)
        l_x = (x * sqrt_price * self.sqrt_upper) / (self.sqrt_upper - sqrt_price)
        return l_x

    def _liq_y_(self, y: float, price: float) -> float:
        if self.lower_price >= price:
            return np.inf
        sqrt_price = np.sqrt(price)
        l_y = y / (sqrt_price - self.sqrt_lower)
        return l_y

    def _liq_(self, x: float, y: float, price: float) -> float:
        adj_price = self._adj_price_(price)
        liq = min(self._liq_x_(x, adj_price), self._liq_y_(y, adj_price))
        return liq

    def _liq_to_x_(self, liq: float, price: float) -> float:
        adj_price = self._adj_price_(price)
        sqrt_price = np.sqrt(adj_price)
        numer = self.sqrt_upper - sqrt_price
        denom = self.sqrt_upper * sqrt_price
        x = liq * numer / denom
        return x

    def _liq_to_y_(self, liq: float, price: float) -> float:
        adj_price = self._adj_price_(price)
        sqrt_price = np.sqrt(adj_price)
        y = liq * (sqrt_price - self.sqrt_lower)
        return y

    def _liq_to_xy_(self, liq: float, price: float) -> Tuple[float, float]:
        x = self._liq_to_x_(liq, price)
        y = self._liq_to_y_(liq, price)
        return x, y

    def _optimal_ratio_(self, price: float) -> float:
        sqrt_price = np.sqrt(price)
        if self.sqrt_upper <= sqrt_price:
            return np.inf
        if self.sqrt_lower >= sqrt_price:
            return 0
        numer = (sqrt_price - self.sqrt_lower) * self.sqrt_upper * sqrt_price
        denom = self.sqrt_upper - sqrt_price
        ratio = numer / denom
        return ratio

    def _liqudity_aligning_(self, x: float, y: float, price: float) -> Tuple[float, float]:
        """implement as swaping mechanics"""
        ratio_opt = self._optimal_ratio_(price)

        if ratio_opt == np.inf:
            return 0, y + price * x * (1 - self.fee_percent)

        dy = ratio_opt * x - y

        if dy >= 0:
            multiplier = 1 - self.fee_percent
        else:
            multiplier = 1 / (1 - self.fee_percent)

        denom = multiplier * price + ratio_opt
        dx = dy / denom
        new_x = x - dx
        new_y = y + multiplier * price * dx
        return new_x, new_y




