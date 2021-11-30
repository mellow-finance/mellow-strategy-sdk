from .UniUtils import UniswapV3Utils
from .Positions import UniV3Position, BiCurrencyPosition
from .primitives import Pool

from abc import ABC, abstractmethod
import math
import numpy as np
import pandas_ta as ta


class AbstractStrategy(ABC):
    """
    ``AbstractStrategy`` is a abstract class for Strategies
    :param name: Unique name for the instance
    """
    def __init__(self, name: str = None):
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name

    @abstractmethod
    def rebalance(self, *args, **kwargs) -> bool:
        '''
        Rebalance implementation
        :param args:
        :param kwargs:
        :return: True if strategy rebalances portfolio or False otherwise
        '''
        raise Exception(NotImplemented)


class BiCurrencyPassive(AbstractStrategy):
    """
    ``BiCurrencyPassive`` is the simplest strategy for asset pair.
    This strategy only tracks own statistic in time
    :param pool: UniswapV3 Pool instance
    :param name: Unique name for the instance
    """
    def __init__(self,
                 pool: Pool,
                 name: str = None,
                 ):
        super().__init__(name)
        self.decimal_diff = -pool.decimals_diff
        self.fees_percent = pool.fee.percent

    def rebalance(self, *args, **kwargs) -> bool:
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        portfolio = kwargs['portfolio']

        price = row['price']

        is_rebalanced = False

        if 'Vault' not in portfolio.positions:
            bicurrency = BiCurrencyPosition('Vault',
                                            0.003,
                                            0.01,
                                            1 / price, 1,
                                            0.0,
                                            0.0)
            portfolio.append(bicurrency)
            is_rebalanced = True

        return is_rebalanced


class BiCurrencyActive(AbstractStrategy):
    """
    ``BiCurrencyActive`` is the strategy for asset pair, that rebalances asset weights over time.
    Weights are calculated by the formula. Rebalancing occurs by a trigger.
    :param bicur_tolerance: UniswapV3 Pool instance
    :param lower_0: Base lower bound of the emulated interval
    :param upper_0: Base upper bound of the emulated interval
    :param rebalance_cost: Rebalancing cost, expressed in currency
    :param x_interest: Interest on  currency X deposit expressed as a daily percentage yield
    :param y_interest: Interest on  currency Y deposit expressed as a daily percentage yield
    :param pool: UniswapV3 Pool instance
    :param name: Unique name for the instance
    """
    def __init__(self,
                 bicur_tolerance: int,
                 window_width: int,
                 lower_0: float,
                 upper_0: float,
                 pool: Pool,
                 rebalance_cost: float,
                 x_interest: float = None,
                 y_interest: float = None,
                 name: str = None,
                 ):

        super().__init__(name)
        self.bicur_tolerance = bicur_tolerance
        self.window_width = window_width
        self.lower_0 = lower_0
        self.upper_0 = upper_0

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

        self.x_interest = x_interest
        self.y_interest = y_interest

        self.prev_rebalance_tick = None
        self.prev_gain_date = None

    def rebalance(self, *args, **kwargs) -> bool:
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        df_swaps_prev = kwargs['prev_data']
        portfolio = kwargs['portfolio']

        price = row['price']
        current_tick = self._price_to_tick_(price)

        mean_price = df_swaps_prev[-self.window_width:]['price'].mean()
        # if df_swaps_prev.shape[0] > self.window_width:
        #     mean_price = ta.ema(df_swaps_prev["price"][-self.window_width:], length=self.window_width).iloc[-1]
        # else:
        #     mean_price = price

        mean_tick = self._price_to_tick_(mean_price)

        is_rebalanced = False

        if 'Vault' not in portfolio.positions:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / price, 1,
                                            self.x_interest,
                                            self.y_interest)
            portfolio.append(bicurrency)
            self.prev_rebalance_tick = current_tick
            is_rebalanced = True

        if self.prev_rebalance_tick is None:
            vault = portfolio.get_position('Vault')
            self.prev_rebalance_tick = self._price_to_tick_(vault.y / vault.x)

        if abs(self.prev_rebalance_tick - mean_tick) >= self.bicur_tolerance:
            vault = portfolio.get_position('Vault')

            fraction_x = self._calc_fraction_to_x_(price, price)
            fraction_y = self._calc_fraction_to_y_(price, price)

            vault.rebalance(fraction_x, fraction_y, price)
            self.prev_rebalance_tick = current_tick
            is_rebalanced = True

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.normalize()

        if timestamp.normalize() > self.prev_gain_date:
            vault = portfolio.get_position('Vault')
            vault.interest_gain(timestamp.normalize())
            self.prev_gain_date = timestamp.normalize()

        return is_rebalanced

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))

    def _calc_fraction_to_x_(self, upper_price, price):
        numer = price / np.sqrt(upper_price) - price / np.sqrt(self.upper_0)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction X = {res}')
        elif res < 0:
            print(f'Warning fraction X = {res}')
        return res

    def _calc_fraction_to_y_(self, lower_price, price):
        numer = np.sqrt(lower_price) - np.sqrt(self.lower_0)
        denom = 2 * np.sqrt(price) - np.sqrt(self.lower_0) - price / np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Y = {res}')
        elif res < 0:
            print(f'Warning fraction Y = {res}')
        return res


class UniV3Passive(AbstractStrategy):
    """
    ``UniV3Passive`` is the passive strategy on UniswapV3 without rebalances.
    :param lower_price: Lower bound of the interval
    :param upper_price: Upper bound of the interval
    :param rebalance_cost: Rebalancing cost, expressed in currency
    :param pool: UniswapV3 Pool instance
    :param name: Unique name for the instance
    """
    def __init__(self,
                 lower_price: float,
                 upper_price: float,
                 pool: Pool,
                 rebalance_cost: float,
                 name: str = None,
                 ):
        super().__init__(name)
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

    def rebalance(self, *args, **kwargs) -> bool:
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        portfolio = kwargs['portfolio']
        price_before, price = row['price_before'], row['price']

        is_rebalanced = False

        if len(portfolio.positions) == 0:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / price, 1,
                                            0.0,
                                            0.0)
            portfolio.append(bicurrency)

        if 'UniV3Passive' in portfolio.positions:
            uni_pos = portfolio.get_position('UniV3Passive')
            uni_pos.charge_fees(price_before, price)

        if 'UniV3Passive' not in portfolio.positions:
            self.create_uni_position(portfolio, price)
            is_rebalanced = True

        return is_rebalanced

    # def create_uni_position(self, price) -> UniV3Position:
    #     uni_fabric = UniswapV3Utils(self.lower_price, self.upper_price)
    #     x_uni_aligned, y_uni_aligned = uni_fabric._align_to_liq_(1 / price, 1, self.lower_price, self.upper_price, price)
    #     univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent, self.rebalance_cost)
    #     univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
    #     return univ3_pos

    def create_uni_position(self, portfolio, price):
        uni_fabric = UniswapV3Utils(0, 1e8)

        vault = portfolio.get_position('Vault')
        x_all, y_all = vault.to_xy(price)

        fraction_uni = uni_fabric._calc_fraction_to_uni_(self.lower_price, self.upper_price, price)
        print('fraction_uni', fraction_uni)
        x_uni, y_uni = x_all * fraction_uni, y_all * fraction_uni
        x_uni_aligned, y_uni_aligned = uni_fabric._align_to_liq_(x_uni, y_uni, self.lower_price, self.upper_price, price)

        vault.withdraw(x_uni_aligned, y_uni_aligned)

        univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent, self.rebalance_cost)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)

        portfolio.append(univ3_pos)
        return None


class UniV3Active(AbstractStrategy):
    """
    ``UniV3Active`` is the strategy for asset pair and UniswapV3 position. Strategy rebalances asset weights over time, and
    Weights are calculated by the formula. Rebalancing occurs by a trigger.
    :param mint_tolerance: The width of the interval of the small neighborhood of the tickspacing
    :param burn_tolerance: Amount of ticks which it is necessary deviate from previous position to trigger rebalancing
    :param grid_width: The width of tickspacing grid
    :param width_num: The width of position interval
    :param lower_0: Base lower bound of the emulated interval
    :param upper_0: Base upper bound of the emulated interval
    :param rebalance_cost: Rebalancing cost, expressed in currency
    :param x_interest: Interest on  currency X deposit expressed as a daily percentage yield
    :param y_interest: Interest on  currency Y deposit expressed as a daily percentage yield
    :param pool: UniswapV3 Pool instance
    :param name: Unique name for the instance
    """
    def __init__(self,
                 signal,
                 # mint_tolerance: int,
                 burn_tolerance: int,
                 grid_width: int,
                 width_num: int,
                 window_width: int,
                 lower_0: float,
                 upper_0: float,
                 pool: Pool,
                 rebalance_cost: float,
                 x_interest: float = None,
                 y_interest: float = None,
                 name: str = None,
                 ):
        super().__init__(name)
        # self.mint_tolerance = mint_tolerance
        self.signal = signal
        self.burn_tolerance = burn_tolerance

        self.grid_width = grid_width
        self.width_num = width_num
        self.window_width = window_width

        self.lower_0 = lower_0
        self.upper_0 = upper_0

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

        self.x_interest = x_interest
        self.y_interest = y_interest

        self.previous_uni_tick = None
        # self.prev_rebalance_tick = None
        self.prev_gain_date = None

    def rebalance(self, *args, **kwargs) -> bool:
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        df_swaps_prev = kwargs['prev_data']
        portfolio = kwargs['portfolio']

        price_before, price = row['price_before'], row['price']
        current_tick = self._price_to_tick_(price)

        mean_price = df_swaps_prev[-self.window_width:]['price'].mean()
        mean_tick = self._price_to_tick_(mean_price)

        lower_tick, center_tick, upper_tick = self._get_bounds_(current_tick)
        lower_price = self._tick_to_price_(lower_tick)
        upper_price = self._tick_to_price_(upper_tick)

        is_rebalanced = False

        if len(portfolio.positions) == 0:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / price, 1,
                                            self.x_interest,
                                            self.y_interest)
            portfolio.append(bicurrency)
            # self.prev_rebalance_tick = current_tick

        # last_pos = portfolio.get_last_position()
        # if hasattr(last_pos, 'charge_fees'):
        #     last_pos.charge_fees(price_before, price)

        for name, pos in portfolio.positions.items():
            if 'Uni' in name:
                pos.charge_fees(price_before, price)

        if len(portfolio.positions) > 1:
            if abs(self.previous_uni_tick - mean_tick) >= self.burn_tolerance:
                self.remove_uni_position(timestamp, portfolio, price)
                is_rebalanced = True

        if len(portfolio.positions) < 2:
            # if abs(current_tick - center_tick) <= self.mint_tolerance:
            idx = self.signal.index[self.signal.index.get_loc(timestamp, method='nearest')]
            if self.signal[idx] >= 1:
                self.create_uni_position(f'UniV3_{timestamp}', portfolio, lower_price, upper_price, price)
                self.previous_uni_tick = center_tick
                is_rebalanced = True

        return is_rebalanced

    def remove_uni_position(self, timestamp, portfolio, price) -> None:
        last_pos = portfolio.get_last_position()
        x_out, y_out = last_pos.withdraw(price)
        portfolio.remove(last_pos.name)
        portfolio.get_position('Vault').deposit(x_out, y_out)

        # uni_fabric = UniV3Fabric(self.portfolio, self.lower_0, self.upper_0, self.fee_percent, self.rebalance_cost)
        # fraction_x = uni_fabric._calc_fraction_to_x_(price, price)
        # fraction_y = uni_fabric._calc_fraction_to_y_(price, price)
        #
        # self.portfolio.get_position('Vault').rebalance(fraction_x, fraction_y, price)
        return None

    def create_uni_position(self, name, portfolio, lower_price, upper_price, price):
        uni_fabric = UniswapV3Utils(self.lower_0, self.upper_0)

        vault = portfolio.get_position('Vault')
        x_all, y_all = vault.to_xy(price)

        fraction_uni = uni_fabric._calc_fraction_to_uni_(lower_price, upper_price, price)
        print('fraction_uni', fraction_uni)
        x_uni, y_uni = x_all * fraction_uni, y_all * fraction_uni

        # x_uni_aligned, y_uni_aligned = uni_fabric._align_to_liq_(x_uni, y_uni, lower_price, upper_price, price)
        # vault.withdraw(x_uni_aligned, y_uni_aligned)

        vault.withdraw(x_uni, y_uni)
        x_uni_aligned, y_uni_aligned = uni_fabric._align_to_liq_(x_uni, y_uni, lower_price, upper_price, price)
        # vault.withdraw(x_uni_aligned, y_uni_aligned)


        univ3_pos = UniV3Position(name, lower_price, upper_price, self.fee_percent, self.rebalance_cost)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
        portfolio.append(univ3_pos)

        # fraction_x = uni_fabric._calc_fraction_to_x_(upper_price, price) / (1 - fraction_uni)
        # fraction_y = uni_fabric._calc_fraction_to_y_(lower_price, price) / (1 - fraction_uni)
        # vault.rebalance(fraction_x, fraction_y, price)
        return None

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
