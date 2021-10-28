from .Backtest import AbstractStrategy
from strategy.Portfolio import Portfolio
from .primitives import Pool
from .Fabrics import UniswapV3Fabric
from .Positions import UniV3Position

import math
import numpy as np
import pandas as pd


class BiCurrency(AbstractStrategy):
    def __init__(self,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):

        super().__init__(portfolio)

        self.decimal_diff = -pool.decimals_diff
        self.fees_percent = pool.fee.percent

    def rebalance(self, *args, **kwargs) -> None:
        pass

    def snapshot(self, date, price: float) -> dict:
        snapshot = self.portfolio.snapshot(date, price)
        return snapshot


class BiCurrencyEqualized(AbstractStrategy):
    def __init__(self,
                 bicur_tolerance: int,
                 lower_0: float,
                 upper_0: float,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):

        super().__init__(portfolio)
        self.bicur_tolerance = bicur_tolerance

        self.lower_0 = lower_0
        self.upper_0 = upper_0

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent

        self.prev_rebalance_tick = None
        self.prev_gain_date = None


    def rebalance(self, *args, **kwargs) -> None:
        timestamp, row = kwargs['timestamp'], kwargs['row']
        price = row['price']

        current_tick = self._price_to_tick_(price)

        if self.prev_rebalance_tick is None:
            if self.portfolio.positions:
                vault = self.portfolio.get_position('Vault')
                self.prev_rebalance_tick = self._price_to_tick_(vault.y / vault.x)

        if abs(self.prev_rebalance_tick - current_tick) >= self.bicur_tolerance:
            vault = self.portfolio.get_position('Vault')

            uni_fabric = UniswapV3Fabric(self.portfolio, self.lower_0, self.upper_0, self.fee_percent)
            fraction_x = uni_fabric._calc_fraction_to_x_(price, price)
            fraction_y = uni_fabric._calc_fraction_to_y_(price, price)

            vault.rebalance(fraction_x, fraction_y, price)
            self.prev_rebalance_tick = current_tick

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.normalize()

        if timestamp.normalize() > self.prev_gain_date:
            vault = self.portfolio.get_position('Vault')
            vault.interest_gain(timestamp.normalize())
            self.prev_gain_date = timestamp.normalize()

        return None

    def snapshot(self, date, price: float) -> dict:
        snapshot = self.portfolio.snapshot(date, price)
        return snapshot

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))


class UniV3Passive(AbstractStrategy):
    def __init__(self,
                 x: float,
                 y: float,
                 lower_price: float,
                 upper_price: float,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):
        super().__init__(portfolio)
        self.x = x
        self.y = y
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent

    def rebalance(self, *args, **kwargs) -> None:
        timestamp, row = kwargs['timestamp'], kwargs['row']
        price_before, price = row['price_before'], row['price']

        if len(self.portfolio.positions) == 1:
            uni_pos = self.portfolio.get_position('UniV3Passive')
            uni_pos.charge_fees(price_before, price)

        if len(self.portfolio.positions) == 0:
            self.create_uni_pos(self.x, self.y, price)

        return None

    def create_uni_pos(self, x, y, price) -> None:
        uni_fabric = UniswapV3Fabric(self.portfolio, self.lower_price, self.upper_price, self.fee_percent)
        x_uni_aligned, y_uni_aligned = uni_fabric._align_to_liq_(x, y, self.lower_price, self.upper_price, price)
        univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
        self.portfolio.append(univ3_pos)
        return None

    def snapshot(self, date, price: float) -> dict:
        snapshot = self.portfolio.snapshot(date, price)
        return snapshot

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))


class UniV3Active(AbstractStrategy):
    def __init__(self,
                 mint_tolerance: int,
                 burn_tolerance: int,
                 grid_width: int,
                 width_num: int,
                 lower_0: float,
                 upper_0: float,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):
        super().__init__(portfolio)
        self.mint_tolerance = mint_tolerance
        self.burn_tolerance = burn_tolerance

        self.grid_width = grid_width
        self.width_num = width_num

        self.lower_0 = lower_0
        self.upper_0 = upper_0

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent

        self.previous_uni_tick = None
        self.withdraw = False

    def rebalance(self, *args, **kwargs) -> None:
        timestamp, row = kwargs['timestamp'], kwargs['row']
        price_before, price = row['price_before'], row['price']

        current_tick = self._price_to_tick_(price)
        lower_tick, center_tick, upper_tick = self._get_bounds_(current_tick)

        lower_price = self._tick_to_price_(lower_tick)
        upper_price = self._tick_to_price_(upper_tick)

        last_pos = self.portfolio.get_last_position()
        if hasattr(last_pos, 'charge_fees'):
            last_pos.charge_fees(price_before, price)

        if self.previous_uni_tick is None:
            self.create_uni_pos(f'UniV3_{timestamp}', lower_price, upper_price, price)
            self.previous_uni_tick = center_tick

        if len(self.portfolio.positions) > 1:
        # if not self.withdraw:
            if abs(self.previous_uni_tick - current_tick) >= self.burn_tolerance:
                self.remove_uni_pos(timestamp, price)
                self.withdraw = True

        if len(self.portfolio.positions) < 2:
            if abs(current_tick - center_tick) <= self.mint_tolerance:
                self.create_uni_pos(f'UniV3_{timestamp}', lower_price, upper_price, price)
                self.previous_uni_tick = center_tick
        return None

    def remove_uni_pos(self, timestamp, price) -> None:
        last_pos = self.portfolio.get_last_position()
        x_out, y_out = last_pos.withdraw(price)
        self.portfolio.remove(last_pos.name)
        self.portfolio.get_position('Vault').deposit(x_out, y_out)

        uni_fabric = UniswapV3Fabric(self.portfolio, self.lower_0, self.upper_0, self.fee_percent)
        fraction_x = uni_fabric._calc_fraction_to_x_(price, price)
        fraction_y = uni_fabric._calc_fraction_to_y_(price, price)

        self.portfolio.get_position('Vault').rebalance(fraction_x, fraction_y, price)
        return None

    def create_uni_pos(self, name, lower_price, upper_price, price) -> None:
        uni_fabric = UniswapV3Fabric(self.portfolio, self.lower_0, self.upper_0, self.fee_percent)
        uni_v3_pos = uni_fabric.create_uni_position(name, lower_price, upper_price, price)
        self.portfolio.append(uni_v3_pos)
        return None

    def snapshot(self, date, price: float) -> dict:
        snapshot = self.portfolio.snapshot(date, price)
        return snapshot

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))

    def _get_bounds_(self, current_tick):
        center_num = int(round(current_tick / self.grid_width))
        center_tick = self.grid_width * center_num
        tick_lower_bound = self.grid_width * (center_num - self.width_num)
        tick_upper_bound = self.grid_width * (center_num + self.width_num)
        # print(f"Lower = {tick_lower_bound}, center={center_tick}, upper={tick_upper_bound}")
        return tick_lower_bound, center_tick, tick_upper_bound
