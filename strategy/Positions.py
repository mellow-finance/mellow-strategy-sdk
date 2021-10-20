from typing import Tuple
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime


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

    @abstractmethod
    def snapshot(self, date: datetime, price: float) -> None:
        raise Exception(NotImplemented)


class BiCurrencyPosition(AbstractPosition):
    def __init__(self, name: str,
                 swap_fee: float,
                 x: float = None,
                 y: float = None,
                 ) -> None:
        super().__init__(name)

        self.x = x if x is not None else 0
        self.y = y if y is not None else 0

        self.swap_fee = swap_fee

        # history variables
        self.history_x = {}
        self.history_y = {}
        self.history_to_x = {}
        self.history_to_y = {}

    def deposit(self, x: float, y: float) -> None:
        self.x += x
        self.y += y
        return None

    def withdraw(self, x: float, y: float) -> Tuple[float, float]:
        self.x -= x
        self.y -= y
        return x, y

    def withdraw_fraction(self, fraction: float) -> Tuple[float, float]:
        x_out, y_out = self.withdraw(self.x * fraction, self.y * fraction)
        return x_out, y_out

    def equalize(self, price: float) -> None:
        dV = price * self.x - self.y
        denom = 2 - self.swap_fee
        if dV > 0:
            dx = dV / (price * denom)
            self.swap_x_to_y(dx, price)

        elif dV < 0:
            dy = abs(dV) / denom
            self.swap_y_to_x(dy, price)

        return None

    # def equalize(self, price: float) -> None:
    #     v = price * self.x + self.y
    #     x_new = v / (2*price)
    #     y_new = v / 2
    #     self.x = x_new
    #     self.y = y_new
    #     return None

    def to_x(self, price: float) -> float:
        res = self.x + self.y / price
        return res

    def to_y(self, price: float) -> float:
        res = self.x * price + self.y
        return res

    def to_xy(self, price: float) -> Tuple[float, float]:
        return self.x, self.y

    def swap_x_to_y(self, dx: float, price: float) -> None:
        self.x -= dx
        self.y += price * (1 - self.swap_fee) * dx
        return None

    def swap_y_to_x(self, dy: float, price: float) -> None:
        self.y -= dy
        self.x += (1 - self.swap_fee) * dy / price
        return None

    def snapshot(self, date: datetime, price: float) -> None:
        x, y = self.to_xy(price)
        volume_x = self.to_x(price)
        volume_y = self.to_y(price)

        self.history_x[date] = x
        self.history_y[date] = y

        self.history_to_x[date] = volume_x
        self.history_to_y[date] = volume_y
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
        self.bi_currency = BiCurrencyPosition('Virtual', self.fee_percent)

        self.realized_loss_to_x = 0
        self.realized_loss_to_y = 0

        self.fees_x = 0
        self._fees_x_earned_ = 0

        self.fees_y = 0
        self._fees_y_earned_ = 0

        # history variables
        self.history_x = {}
        self.history_y = {}

        self.history_to_x = {}
        self.history_to_y = {}

        self.history_fees_x = {}
        self.history_fees_y = {}

        self.history_fees_to_x = {}
        self.history_fees_to_y = {}

        self.history_il_to_x = {}
        self.history_il_to_y = {}

        self.history_earned_fees_x = {}
        self.history_earned_fees_y = {}

        self.history_earned_fees_to_x = {}
        self.history_earned_fees_to_y = {}

        self.history_realized_loss_to_x = {}
        self.history_realized_loss_to_y = {}

    def deposit(self, x: float, y: float, price: float) -> None:
        self.mint(x, y, price)
        return None

    def withdraw(self, price: float) -> Tuple[float, float]:
        x_out, y_out = self.burn(self.liquidity, price)
        x_fees, y_fees = self.collect_fees()
        x_res, y_res = x_out + x_fees, y_out + y_fees
        return x_res, y_res

    def mint(self, x: float, y: float, price: float) -> None:
        x_aligned, y_aligned = self._liqudity_aligning_(x, y, price)
        self.bi_currency.deposit(x_aligned, y_aligned)
        dliq = self._xy_to_liq_(x_aligned, y_aligned, price)
        self.liquidity += dliq
        return None

    def burn(self, liq: float, price: float) -> Tuple[float, float]:
        il_x_0 = self.impermanent_loss_to_x(price)
        il_y_0 = self.impermanent_loss_to_y(price)

        x_out, y_out = self._liq_to_xy_(liq, price)

        self.bi_currency.withdraw_fraction(liq / self.liquidity)
        self.liquidity -= liq

        il_x_1 = self.impermanent_loss_to_x(price)
        il_y_1 = self.impermanent_loss_to_y(price)

        self.realized_loss_to_x += (il_x_0 - il_x_1)
        self.realized_loss_to_y += (il_y_0 - il_y_1)
        return x_out, y_out

    def charge_fees(self, price_0: float, price_1: float) -> None:
        price_0_adj = self._adj_price_(price_0)
        price_1_adj = self._adj_price_(price_1)

        x_0, y_0 = self.to_xy(price_0_adj)
        x_1, y_1 = self.to_xy(price_1_adj)

        fee_x, fee_y = 0, 0
        if y_0 >= y_1:
            fee_x = (x_1 - x_0) * self.fee_percent
            if fee_x < 0:
                print('NEGATIVE X:', fee_x)
        else:
            fee_y = (y_1 - y_0) * self.fee_percent
            if fee_y < 0:
                print('NEGATIVE Y:', fee_y)

        self.fees_x += fee_x
        self._fees_x_earned_ += fee_x

        self.fees_y += fee_y
        self._fees_y_earned_ += fee_y
        return None

    def collect_fees(self) -> Tuple[float, float]:
        fees_x = self.fees_x
        fees_y = self.fees_y
        self.fees_x = 0
        self.fees_y = 0
        return fees_x, fees_y

    def reinvest_fees(self, price) -> None:
        fees_x, fees_y = self.collect_fees()
        self.mint(fees_x, fees_y, price)
        return None

    def impermanent_loss(self, price: float) -> Tuple[float, float]:
        x_hold, y_hold = self.bi_currency.to_xy(price)
        x_stake, y_stake = self.to_xy(price)
        il_x = x_hold - x_stake
        il_y = y_hold - y_stake
        return il_x, il_y

    def impermanent_loss_to_x(self, price: float) -> float:
        v_hold = self.bi_currency.to_x(price)
        v_stake = self.to_x(price)
        il_x = v_hold - v_stake
        return il_x

    def impermanent_loss_to_y(self, price: float) -> float:
        v_hold = self.bi_currency.to_y(price)
        v_stake = self.to_y(price)
        il_y = v_hold - v_stake
        return il_y

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

    def snapshot(self, date: datetime, price: float) -> None:
        x, y = self.to_xy(price)
        self.history_x[date] = x
        self.history_y[date] = y

        volume_x = self.to_x(price)
        self.history_to_x[date] = volume_x

        volume_y = self.to_y(price)
        self.history_to_y[date] = volume_y

        self.history_fees_x[date] = self.fees_x
        self.history_fees_y[date] = self.fees_y

        volume_fees_x = self.fees_x + self.fees_y / price
        self.history_fees_to_x[date] = volume_fees_x

        volume_fees_y = price * self.fees_x + self.fees_y
        self.history_fees_to_y[date] = volume_fees_y

        il_x = self.impermanent_loss_to_x(price)
        self.history_il_to_x[date] = il_x

        il_y = self.impermanent_loss_to_y(price)
        self.history_il_to_y[date] = il_y

        self.history_earned_fees_x[date] = self._fees_x_earned_
        self.history_earned_fees_y[date] = self._fees_y_earned_

        _total_fees_earned_x_ = self._fees_x_earned_ + self._fees_y_earned_ / price
        self.history_earned_fees_to_x[date] = _total_fees_earned_x_

        _total_fees_earned_y_ = price * self._fees_x_earned_ + self._fees_y_earned_
        self.history_earned_fees_to_y[date] = _total_fees_earned_y_

        self.history_realized_loss_to_x[date] = self.realized_loss_to_x
        self.history_realized_loss_to_y[date] = self.realized_loss_to_y

        return None

    def _adj_price_(self, price: float) -> float:
        adj_price = min(max(self.lower_price, price), self.upper_price)
        return adj_price

    def _x_to_liq_(self, x: float, price: float) -> float:
        if self.upper_price <= price:
            return np.inf
        sqrt_price = np.sqrt(price)
        l_x = (x * sqrt_price * self.sqrt_upper) / (self.sqrt_upper - sqrt_price)
        return l_x

    def _y_to_liq_(self, y: float, price: float) -> float:
        if self.lower_price >= price:
            return np.inf
        sqrt_price = np.sqrt(price)
        l_y = y / (sqrt_price - self.sqrt_lower)
        return l_y

    def _xy_to_liq_(self, x: float, y: float, price: float) -> float:
        adj_price = self._adj_price_(price)
        liq = min(self._x_to_liq_(x, adj_price), self._y_to_liq_(y, adj_price))
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



    # def _impermanent_loss_(self, liq: float, price: float, price_init: float) -> float:
    #     sqrt_price_init = np.sqrt(price_init)
    #     volume_y_held = liq * (sqrt_price_init - self.sqrt_lower + price * (1 / sqrt_price_init - 1 / self.sqrt_upper))
    #     x_stake, y_stake = self._liq_to_xy_(liq, price)
    #     volume_y_held_staked = x_stake * price + y_stake
    #     il_y = volume_y_held - volume_y_held_staked
    #     return il_y