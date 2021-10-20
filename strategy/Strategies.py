from .Backtest import AbstractStrategy
from strategy.Portfolio import Portfolio
from .primitives import Pool
from strategy.Positions import UniV3Position

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

    def snapshot(self, date, price: float) -> None:
        self.portfolio.snapshot(date, price)
        return None


class BiCurrencyEqualized(AbstractStrategy):
    def __init__(self,
                 bicur_tolerance: int,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):

        super().__init__(portfolio)
        self.bicur_tolerance = bicur_tolerance

        self.decimal_diff = -pool.decimals_diff
        self.fees_percent = pool.fee.percent

        self.prev_rebalance_tick = None

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
            vault.equalize(price)
            self.prev_rebalance_tick = current_tick

        return None

    def snapshot(self, date, price: float) -> None:
        self.portfolio.snapshot(date, price)
        return None

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))


class UniV2(AbstractStrategy):
    def __init__(self,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):
        super().__init__(portfolio)
        self.decimal_diff = pool.decimals_diff
        self.fees_percent = pool.fee.percent

        self.reinvest_prev_timestamp = pd.Timestamp('2021-05-04')

    def rebalance(self, *args, **kwargs) -> None:
        timestamp, row = kwargs['timestamp'], kwargs['row']
        price_0, price_1 = row['price_before'], row['price']

        uni_pos = self.portfolio.get_position('UniV2')
        uni_pos.charge_fees(price_0, price_1)

        if self.reinvest_prev_timestamp < timestamp.normalize():
            uni_pos.reinvest_fees(price_1)
            self.reinvest_prev_timestamp = timestamp.normalize()

        return None

    def snapshot(self, date, price: float) -> None:
        self.portfolio.snapshot(date, price)
        return None

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))


class UniV3(AbstractStrategy):
    def __init__(self,
                 mint_tolerance: int,
                 burn_tolerance: int,
                 grid_width: int,
                 grid_num: int,
                 pool: Pool,
                 portfolio: Portfolio = None,
                 ):
        super().__init__(portfolio)
        self.mint_tolerance = mint_tolerance
        self.burn_tolerance = burn_tolerance

        self.grid_width = grid_width
        self.grid_num = grid_num

        self.decimal_diff = pool.decimals_diff
        self.fees_percent = pool.fee.percent

        self.previous_uni_tick = None

    def rebalance(self, *args, **kwargs) -> None:
        timestamp, row = kwargs['timestamp'], kwargs['row']
        price_0, price_1 = row['price_before'], row['price']
        current_tick = self._price_to_tick_(price_1)
        lower_tick, center_tick, upper_tick = self._get_bounds_(price_1, self.grid_width, self.grid_num)

        last_pos = self.portfolio.get_last_position()
        if hasattr(last_pos, 'charge_fees'):
            last_pos.charge_fees(price_0, price_1)

        if abs(current_tick - center_tick) < self.mint_tolerance:
            if self.previous_uni_tick is None:
                univ3_pos = self.create_uni_pos(timestamp, lower_tick, upper_tick, price_1)
                self.portfolio.append(univ3_pos)
                self.previous_uni_tick = center_tick
            else:
                diff = abs(self.previous_uni_tick - current_tick)
                if self.burn_tolerance < diff:
                    last_pos = self.portfolio.get_last_position()
                    x_out, y_out = last_pos.withdraw(price_1)
                    self.portfolio.snapshot(timestamp.normalize(), price_1)
                    self.portfolio.remove(last_pos.name)

                    self.portfolio.get_position('Vault').deposit(x_out, y_out)
                    self.portfolio.get_position('Vault').equalize(price_1)

                    univ3_pos = self.create_uni_pos(timestamp, lower_tick, upper_tick, price_1)
                    self.portfolio.append(univ3_pos)

                    self.previous_uni_tick = center_tick
        return None

    def create_uni_pos(self, timestamp, lower_tick, upper_tick, price):
        fraction = 0.1
        #         1.001**((tick_upper_bound - tick_lower_bound) / 2) - 1
        x_fraction, y_fraction = self.portfolio.get_position('Vault').withdraw_fraction(fraction)

        lower_price = self._tick_to_price_(lower_tick)
        upper_price = self._tick_to_price_(upper_tick)

        univ3_pos = UniV3Position(f'UniV3_{timestamp}', lower_price, upper_price, self.fees_percent)
        univ3_pos.deposit(x_fraction, y_fraction, price)
        return univ3_pos

    def snapshot(self, date, price: float) -> None:
        self.portfolio.snapshot(date, price)
        return None

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))

    def _get_bounds_(self, price, grid_width, width_num):
        current_tick = self._price_to_tick_(price)
        center_num = int(current_tick // grid_width)
        center_tick = grid_width * center_num

        tick_lower_bound = grid_width * (center_num - width_num)
        tick_upper_bound = grid_width * (center_num + width_num)
        return tick_lower_bound, center_tick, tick_upper_bound