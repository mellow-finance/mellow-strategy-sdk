from .UniUtils import UniswapV3Utils, UniswapV2Utils, UniswapLiquidityAligner
from .Positions import UniV3Position, BiCurrencyPosition
from .primitives import Pool

from abc import ABC, abstractmethod
import math
import numpy as np


class AbstractStrategy(ABC):
    """
    ``AbstractStrategy`` is an abstract class for Strategies.
    Attributes:
        name: Unique name for the instance.
    """
    def __init__(self, name: str = None):
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name

    @abstractmethod
    def rebalance(self, *args, **kwargs) -> bool:
        """
        Rebalance implementation.
        Args:
            args: Any args.
            kwargs: Any kwargs.
        Returns:
            True if strategy rebalances portfolio or False otherwise
        """
        raise Exception(NotImplemented)


class HBStrategy(AbstractStrategy):
    """
    ``HBStrategy`` is the strategy for asset pair, that rebalances asset weights over time.
    Weights are calculated by the formula. Rebalancing occurs by a trigger.
    Attributes:
        bicur_tolerance: UniswapV3 Pool instance.
        pool: UniswapV3 Pool instance.
        rebalance_cost: Rebalancing cost, expressed in currency.
        x_interest: Interest on  currency X deposit expressed as a daily percentage yield.
        y_interest: Interest on  currency Y deposit expressed as a daily percentage yield.
        name: Unique name for the instance.
    """
    def __init__(self,
                 bicur_tolerance: int,
                 window_width: int,
                 pool: Pool,
                 rebalance_cost: float,
                 x_interest: float = None,
                 y_interest: float = None,
                 name: str = None,
                 ):
        super().__init__(name)
        self.bicur_tolerance = bicur_tolerance
        self.window_width = window_width

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

        self.x_interest = x_interest
        self.y_interest = y_interest

        self.prev_rebalance_tick = None
        self.prev_gain_date = None

    def prepare_data(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        df_swaps_prev = kwargs['prev_data']

        price, price_next = row['price'], row['price_next']
        current_tick = self._price_to_tick_(price)

        mean_price_df = df_swaps_prev[-5 * self.window_width:].resample(f'{self.window_width}min')['price'].mean().ffill()
        idx = mean_price_df.index[mean_price_df.index.get_loc(timestamp, method='nearest')]
        mean_price = mean_price_df[idx]
        mean_tick = self._price_to_tick_(mean_price)

        output = {'current_tick': current_tick,
                  'price': price,
                  'price_next': price_next,
                  'mean_tick': mean_tick}
        return output

    def rebalance(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']
        # prepare data for strategy
        params = self.prepare_data(*args, **kwargs)

        is_rebalanced = None

        # if portfolio is empty initilize it with bi-currency position
        if 'Vault' not in portfolio.positions:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / params['price'], 1,
                                            self.x_interest,
                                            self.y_interest)
            portfolio.append(bicurrency)
            self.prev_rebalance_tick = params['current_tick']

        if self.prev_rebalance_tick is None:
            vault = portfolio.get_position('Vault')
            self.prev_rebalance_tick = self._price_to_tick_(vault.y / vault.x)

        if abs(self.prev_rebalance_tick - params['mean_tick']) >= self.bicur_tolerance:
            vault = portfolio.get_position('Vault')
            vault.rebalance(1 / 2, 1 / 2, params['price_next'])
            self.prev_rebalance_tick = params['mean_tick']
            is_rebalanced = 'rebalance'

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.normalize()

        if timestamp.normalize() > self.prev_gain_date:
            vault = portfolio.get_position('Vault')
            vault.interest_gain(timestamp.normalize())
            self.prev_gain_date = timestamp.normalize()

        return is_rebalanced

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))


class HUStrategy(AbstractStrategy):
    """
    ``HUStrategy`` is the strategy for asset pair and UniswapV3 position. Strategy rebalances asset weights over time, and
    Weights are calculated by the formula. Rebalancing occurs by a trigger.
    Attributes:
        mint_tolerance: The width of the interval of the small neighborhood of the tickspacing.
        burn_tolerance: Amount of ticks which it is necessary deviate from previous position to trigger rebalancing.
        grid_width: The width of tickspacing grid.
        width_num: The width of position interval.
        window_width: The width of window for average.
        pool: UniswapV3 Pool instance.
        rebalance_cost: Rebalancing cost, expressed in currency.
        name: Unique name for the instance.
    """
    def __init__(self,
                 mint_tolerance: int,
                 burn_tolerance: int,
                 grid_width: int,
                 width_num: int,
                 window_width: int,
                 pool: Pool,
                 rebalance_cost: float,
                 name: str = None,
                 ):

        super().__init__(name)
        self.mint_tolerance = mint_tolerance
        self.burn_tolerance = burn_tolerance

        self.grid_width = grid_width
        self.width_num = width_num
        self.window_width = window_width

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

        self.previous_uni_tick = None

    def prepare_data(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        df_swaps_prev = kwargs['prev_data']

        price_before, price, price_next = row['price_before'], row['price'], row['price_next']
        current_tick = self._price_to_tick_(price)

        mean_price_df = df_swaps_prev[-5 * self.window_width:].resample(f'{self.window_width}min')['price'].mean().ffill()
        idx = mean_price_df.index[mean_price_df.index.get_loc(timestamp, method='nearest')]
        mean_price = mean_price_df[idx]
        mean_tick = self._price_to_tick_(mean_price)

        lower_tick, center_tick, upper_tick = self._get_bounds_(current_tick)
        lower_price = self._tick_to_price_(lower_tick)
        upper_price = self._tick_to_price_(upper_tick)

        output = {'price': price,
                  'price_before': price_before,
                  'price_next': price_next,
                  'center_tick': center_tick,
                  'lower_price': lower_price,
                  'upper_price': upper_price,
                  'mean_tick': mean_tick}
        return output

    def rebalance(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']
        # prepare data for strategy
        params = self.prepare_data(*args, **kwargs)

        is_rebalanced = None

        # if portfolio is empty initilize it with bi-currency position
        if len(portfolio.positions) == 0:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / params['price'],
                                            1)
            portfolio.append(bicurrency)

        # get fees for swap
        for name, pos in portfolio.positions.items():
            if 'Uni' in name:
                pos.charge_fees(params['price_before'], params['price'])

        # if mean price deviated too much from previous uni position - burn uni position
        if len(portfolio.positions) > 1:
            if abs(self.previous_uni_tick - params['mean_tick']) >= self.burn_tolerance:
                self.remove_last_uni_position(portfolio, params['price_next'])
                is_rebalanced = 'burn'

        # if you could mint the position - mint uni position
        if len(portfolio.positions) < 2:
            if abs(params['mean_tick'] - params['center_tick']) <= self.mint_tolerance:
                # idx = self.signal.index[self.signal.index.get_loc(timestamp, method='nearest')]
                # if self.signal[idx] >= 1:
                self.create_uni_position(f'UniV3_{timestamp}', portfolio,
                                         params['lower_price'], params['upper_price'], params['price_next'])
                self.previous_uni_tick = params['mean_tick']
                is_rebalanced = 'mint'

        return is_rebalanced

    def remove_last_uni_position(self, portfolio, price) -> None:
        last_pos = portfolio.get_last_position()
        x_out, y_out = last_pos.withdraw(price)
        portfolio.remove(last_pos.name)
        portfolio.get_position('Vault').deposit(x_out, y_out)
        return None

    def create_uni_position(self, name, portfolio, lower_price, upper_price, price):
        uni_utils = UniswapV2Utils()
        fraction_uni = uni_utils.calc_fraction_to_uni(price, lower_price, upper_price)

        vault = portfolio.get_position('Vault')
        x_uni, y_uni = vault.withdraw_fraction(fraction_uni)

        uni_aligner = UniswapLiquidityAligner(lower_price, upper_price)
        x_uni_aligned, y_uni_aligned = uni_aligner.align_to_liq(x_uni, y_uni,  price)
        
        univ3_pos = UniV3Position(name, lower_price, upper_price, self.fee_percent, self.rebalance_cost)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
        portfolio.append(univ3_pos)
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
        return tick_lower_bound, center_tick, tick_upper_bound


class MBStrategy(AbstractStrategy):
    """
    ``MBStrategy`` is the strategy for asset pair, that rebalances asset weights over time.
    Weights are calculated by the formula. Rebalancing occurs by a trigger.
    Attributes:
        bicur_tolerance: UniswapV3 Pool instance.
        lower_0: Base lower bound of the emulated interval.
        upper_0: Base upper bound of the emulated interval.
        pool: UniswapV3 Pool instance.
        rebalance_cost: Rebalancing cost, expressed in currency.
        x_interest: Interest on  currency X deposit expressed as a daily percentage yield.
        y_interest: Interest on  currency Y deposit expressed as a daily percentage yield.
        name: Unique name for the instance.
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

    def prepare_data(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        df_swaps_prev = kwargs['prev_data']

        price, price_next = row['price'], row['price_next']
        current_tick = self._price_to_tick_(price)

        mean_price_df = df_swaps_prev[-5 * self.window_width:].resample(f'{self.window_width}min')['price'].mean().ffill()
        idx = mean_price_df.index[mean_price_df.index.get_loc(timestamp, method='nearest')]
        mean_price = mean_price_df[idx]
        mean_tick = self._price_to_tick_(mean_price)

        output = {'current_tick': current_tick,
                  'price': price,
                  'price_next': price_next,
                  'mean_tick': mean_tick}
        return output

    def rebalance(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']
        # prepare data for strategy
        params = self.prepare_data(*args, **kwargs)

        is_rebalanced = None

        # if portfolio is empty initilize it with bi-currency position
        if 'Vault' not in portfolio.positions:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / params['price'], 1,
                                            self.x_interest,
                                            self.y_interest)
            portfolio.append(bicurrency)
            self.prev_rebalance_tick = params['current_tick']

        if self.prev_rebalance_tick is None:
            vault = portfolio.get_position('Vault')
            self.prev_rebalance_tick = self._price_to_tick_(vault.y / vault.x)

        if abs(self.prev_rebalance_tick - params['mean_tick']) >= self.bicur_tolerance:
            fraction_x = self.calc_fraction_to_x(params['price'])
            fraction_y = self.calc_fraction_to_y(params['price'])
            vault = portfolio.get_position('Vault')
            vault.rebalance(fraction_x, fraction_y, params['price_next'])
            self.prev_rebalance_tick = params['mean_tick']
            is_rebalanced = 'rebalance'

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.normalize()

        if timestamp.normalize() > self.prev_gain_date:
            vault = portfolio.get_position('Vault')
            vault.interest_gain(timestamp.normalize())
            self.prev_gain_date = timestamp.normalize()

        return is_rebalanced

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))

    def calc_fraction_to_x(self, price):
        numer = np.sqrt(price) - np.sqrt(self.upper_0)
        denom = np.sqrt(self.lower_0) - np.sqrt(self.upper_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Y = {res}')
        elif res < 0:
            print(f'Warning fraction Y = {res}')
        return res

    def calc_fraction_to_y(self, price):
        numer = np.sqrt(price) - np.sqrt(self.lower_0)
        denom = np.sqrt(self.upper_0) - np.sqrt(self.lower_0)
        res = numer / denom
        if res > 1:
            print(f'Warning fraction Y = {res}')
        elif res < 0:
            print(f'Warning fraction Y = {res}')
        return res


class MUStrategy(AbstractStrategy):
    """
    ``MUstrategy`` is the strategy for asset pair and UniswapV3 position. Strategy rebalances asset weights over time, and
    Weights are calculated by the formula. Rebalancing occurs by a trigger.
    Attributes:
        mint_tolerance: The width of the interval of the small neighborhood of the tickspacing.
        burn_tolerance: Amount of ticks which it is necessary deviate from previous position to trigger rebalancing.
        grid_width: The width of tickspacing grid.
        width_num: The width of position interval.
        lower_0: Base lower bound of the emulated interval.
        upper_0: Base upper bound of the emulated interval.
        rebalance_cost: Rebalancing cost, expressed in currency.
        x_interest: Interest on  currency X deposit expressed as a daily percentage yield.
        y_interest: Interest on  currency Y deposit expressed as a daily percentage yield.
        pool: UniswapV3 Pool instance.
        name: Unique name for the instance.
    """
    def __init__(self,
                #  signal,
                 mint_tolerance: int,
                 burn_tolerance: int,
                 grid_width: int,
                 width_num: int,
                 window_width: int,
                 lower_0: float,
                 upper_0: float,
                 pool: Pool,
                 rebalance_cost: float,
                 name: str = None,
                 ):
        super().__init__(name)
        self.mint_tolerance = mint_tolerance
        # self.signal = signal
        self.burn_tolerance = burn_tolerance

        self.grid_width = grid_width
        self.width_num = width_num
        self.window_width = window_width

        self.lower_0 = lower_0
        self.upper_0 = upper_0

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

        self.previous_uni_tick = None

    def prepare_data(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        df_swaps_prev = kwargs['prev_data']

        price_before, price, price_next = row['price_before'], row['price'], row['price_next']
        current_tick = self._price_to_tick_(price)

        mean_price_df = df_swaps_prev[-5 * self.window_width:].resample(f'{self.window_width}min')['price'].mean().ffill()
        idx = mean_price_df.index[mean_price_df.index.get_loc(timestamp, method='nearest')]
        mean_price = mean_price_df[idx]
        mean_tick = self._price_to_tick_(mean_price)

        lower_tick, center_tick, upper_tick = self._get_bounds_(current_tick)
        lower_price = self._tick_to_price_(lower_tick)
        upper_price = self._tick_to_price_(upper_tick)

        output = {'price': price,
                  'price_before': price_before,
                  'price_next': price_next,
                  'center_tick': center_tick,
                  'lower_price': lower_price,
                  'upper_price': upper_price,
                  'mean_tick': mean_tick}
        return output

    def rebalance(self, *args, **kwargs) -> bool:
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']
        # prepare data for strategy
        params = self.prepare_data(*args, **kwargs)

        is_rebalanced = None

        if len(portfolio.positions) == 0:
            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            self.rebalance_cost,
                                            1 / params['price'],
                                            1)
            portfolio.append(bicurrency)

        for name, pos in portfolio.positions.items():
            if 'Uni' in name:
                pos.charge_fees(params['price_before'], params['price'])

        if len(portfolio.positions) > 1:
            if abs(self.previous_uni_tick - params['mean_tick']) >= self.burn_tolerance:
                self.remove_last_uni_position(portfolio, params['price_next'])
                is_rebalanced = 'burn'

        if len(portfolio.positions) < 2:
            if abs(params['mean_tick'] - params['center_tick']) <= self.mint_tolerance:
            # idx = self.signal.index[self.signal.index.get_loc(timestamp, method='nearest')]
            # if self.signal[idx] >= 1:
                self.create_uni_position(f'UniV3_{timestamp}', portfolio,
                                         params['lower_price'], params['upper_price'], params['price_next'])
                self.previous_uni_tick = params['mean_tick']
                is_rebalanced = 'mint'

        return is_rebalanced

    def remove_last_uni_position(self, portfolio, price) -> None:
        last_pos = portfolio.get_last_position()
        x_out, y_out = last_pos.withdraw(price)
        portfolio.remove(last_pos.name)
        portfolio.get_position('Vault').deposit(x_out, y_out)
        return None

    def create_uni_position(self, name, portfolio, lower_price, upper_price, price):
        uni_utils = UniswapV3Utils(self.lower_0, self.upper_0)
        fraction_uni = uni_utils.calc_fraction_to_uni(price, lower_price, upper_price)
        
        vault = portfolio.get_position('Vault')
        x_uni, y_uni = vault.withdraw_fraction(fraction_uni)

        uni_aligner = UniswapLiquidityAligner(lower_price, upper_price)
        x_uni_aligned, y_uni_aligned = uni_aligner.align_to_liq(x_uni, y_uni,  price)

        univ3_pos = UniV3Position(name, lower_price, upper_price, self.fee_percent, self.rebalance_cost)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
        portfolio.append(univ3_pos)
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
        return tick_lower_bound, center_tick, tick_upper_bound


class LidoStrategy(AbstractStrategy):
    """
    ``LidoStrategy`` is the strategy for wEth/stEth pair on UniswapV3. Strategy rebalances LP positions on UniswapV3.
     Rebalancing occurs by a trigger.
     Attributes:
        grid_width: The width of tickspacing grid.
        interval_width_num: The width of position interval.
        burn_gap: Amount of ticks which strategy waits for burning strategy.
        pool: UniswapV3 Pool instance.
        name: Unique name for the instance.
    """
    def __init__(self,
                 grid_width: int,
                 interval_width_num: int,
                 burn_gap: int,
                 pool: Pool,
                 name: str = None,
                 ):
        super().__init__(name)
        self.grid_width = grid_width
        self.interval_width_num = interval_width_num
        self.burn_gap = burn_gap
        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent

        self.previous_uni_left = None
        self.previous_uni_right = None

    def prepare_data(self, *args, **kwargs):
        row = kwargs['row']
        # df_swaps_prev = kwargs['prev_data']

        price_before, price, price_next = row['price_before'], row['price'], row['price_next']
        current_tick = self._price_to_tick_(price)
        nearest_tick_spacing, tick_mid_bound, tick_upper_bound = self._get_grid_(current_tick)

        nearest_price_spacing = self._tick_to_price_(nearest_tick_spacing)
        mid_price_spacing = self._tick_to_price_(tick_mid_bound)
        upper_price_spacing = self._tick_to_price_(tick_upper_bound)

        output = {'price': price,
                  'current_tick': current_tick,
                  'price_before': price_before,
                  'price_next': price_next,
                  'nearest_tick_spacing': nearest_tick_spacing,
                  'tick_mid': tick_mid_bound,
                  'tick_upper_bound': tick_upper_bound,
                  'nearest_right_price': nearest_price_spacing,
                  'mid_price': mid_price_spacing,
                  'upper_price': upper_price_spacing
                   }

        return output

    def rebalance(self, *args, **kwargs):
        # prepare data for strategy
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']
        params = self.prepare_data(*args, **kwargs)

        is_rebalanced = None

        if len(portfolio.positions) == 0:
            eth_value = 1 / params['price']
            steth_value = 1

            bicurrency = BiCurrencyPosition('Vault',
                                            self.fee_percent,
                                            0,
                                            eth_value, steth_value,
                                            None,
                                            None)
            portfolio.append(bicurrency)

            uni_left = self.create_uni_position(f'Uni_left_{timestamp}', eth_value, steth_value,
                                                params['nearest_right_price'], params['upper_price'], params['price'])
            portfolio.append(uni_left)
            self.previous_uni_left = [params['nearest_tick_spacing'], params['tick_mid'], params['tick_upper_bound']]

        for name, pos in portfolio.positions.items():
            if 'Uni' in name:
                pos.charge_fees(params['price_before'], params['price'])

        # mint right interval
        if len(portfolio.positions) < 3:
            if params['current_tick'] >= self.previous_uni_left[1]:
                vault = portfolio.get_position('Vault')
                x_uni, y_uni = vault.withdraw_fraction(1)
                uni_right = self.create_uni_position(f'Uni_right_{timestamp}', x_uni, y_uni,
                                                     params['nearest_right_price'], params['upper_price'], params['price'])
                portfolio.append(uni_right)
                self.previous_uni_right = [params['nearest_tick_spacing'], params['tick_mid'], params['tick_upper_bound']]
                is_rebalanced = 'mint'

        # if  price deviated too much from previous uni position - burn uni position
        if len(portfolio.positions) > 2:
            if params['current_tick'] - self.burn_gap >= self.previous_uni_left[2]:
                x_out, y_out = self.remove_left_uni_position(portfolio, timestamp, params['price'])
                vault = portfolio.get_position('Vault')
                vault.deposit(x_out, y_out)
                self.previous_uni_left = self.previous_uni_right
                is_rebalanced = 'burn'

        return is_rebalanced

    def remove_left_uni_position(self, portfolio, timestamp, price) -> tuple:
        position_names_list = portfolio.position_names()

        left_pos_name = [name for name in position_names_list if name.startswith('Uni_left')][0]
        left_pos = portfolio.get_position(left_pos_name)
        x_out, y_out = left_pos.withdraw(price)
        portfolio.remove(left_pos_name)

        right_pos_name = [name for name in position_names_list if name.startswith('Uni_right')][0]
        new_right_name = f'Uni_left_{timestamp}'  # + right_pos_name.split('_')[-1]
        portfolio.rename_position(right_pos_name, new_right_name)

        return x_out, y_out

    def create_uni_position(self, name, x_uni, y_uni, lower_price, upper_price, price):
        uni_aligner = UniswapLiquidityAligner(lower_price, upper_price)
        x_uni_aligned, y_uni_aligned = uni_aligner.align_to_liq(x_uni, y_uni, price)

        univ3_pos = UniV3Position(name, lower_price, upper_price, self.fee_percent, 0)
        univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
        return univ3_pos

    def _tick_to_price_(self, tick):
        price = np.power(1.0001, tick)
        return price

    def _price_to_tick_(self, price):
        tick = math.log(price, 1.0001)
        return int(round(tick))

    def _tick_to_grid_(self, current_tick):
        new_grid_width = self.grid_width * self.interval_width_num
        floor_part = int(current_tick // new_grid_width)
        fractional_part = int(current_tick % new_grid_width)
        fractional_part_binary = 1 if fractional_part >= 1 else 0

        left_bound = floor_part * new_grid_width
        right_bound = (floor_part + fractional_part_binary) * new_grid_width
        return left_bound, right_bound

    def _get_grid_(self, current_tick):
        left_bound, right_bound = self._tick_to_grid_(current_tick)
        # step = int(self.grid_width * self.interval_width_num / 2)
        upper_bound = right_bound + self.grid_width * self.interval_width_num
        mid_tick = (right_bound + upper_bound) / 2
        return right_bound, mid_tick, upper_bound


# class UniV3Passive(AbstractStrategy):
#     """
#     ``UniV3Passive`` is the passive strategy on UniswapV3 without rebalances.
#         lower_price: Lower bound of the interval
#         upper_price: Upper bound of the interval
#         rebalance_cost: Rebalancing cost, expressed in currency
#         pool: UniswapV3 Pool instance
#         name: Unique name for the instance
#     """
#     def __init__(self,
#                  lower_price: float,
#                  upper_price: float,
#                  pool: Pool,
#                  rebalance_cost: float,
#                  name: str = None,
#                  ):
#         super().__init__(name)
#         self.lower_price = lower_price
#         self.upper_price = upper_price
#         self.decimal_diff = -pool.decimals_diff
#         self.fee_percent = pool.fee.percent
#         self.rebalance_cost = rebalance_cost

#     def rebalance(self, *args, **kwargs) -> bool:
#         timestamp = kwargs['timestamp']
#         row = kwargs['row']
#         portfolio = kwargs['portfolio']
#         price_before, price = row['price_before'], row['price']

#         is_rebalanced = False

#         if len(portfolio.positions) == 0:
#             bicurrency = BiCurrencyPosition('Vault',
#                                             self.fee_percent,
#                                             self.rebalance_cost,
#                                             1 / price, 1,
#                                             0.0,
#                                             0.0)
#             portfolio.append(bicurrency)

#         if 'UniV3Passive' in portfolio.positions:
#             uni_pos = portfolio.get_position('UniV3Passive')
#             uni_pos.charge_fees(price_before, price)

#         if 'UniV3Passive' not in portfolio.positions:
#             self.create_uni_position(portfolio, price)
#             is_rebalanced = True

#         return is_rebalanced

#     # def create_uni_position(self, price) -> UniV3Position:
#     #     uni_fabric = UniswapV3Utils(self.lower_price, self.upper_price)
#     #     x_uni_aligned, y_uni_aligned = uni_fabric._align_to_liq_(1 / price, 1, self.lower_price, self.upper_price, price)
#     #     univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent, self.rebalance_cost)
#     #     univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
#     #     return univ3_pos

#     def create_uni_position(self, portfolio, price):
#         uni_fabric = UniswapV3Utils(0, 1e8)

#         vault = portfolio.get_position('Vault')
#         x_all, y_all = vault.to_xy(price)

#         fraction_uni = uni_fabric.calc_fraction_to_uni(self.lower_price, self.upper_price, price)
#         print('fraction_uni', fraction_uni)
#         x_uni, y_uni = x_all * fraction_uni, y_all * fraction_uni
#         x_uni_aligned, y_uni_aligned = uni_fabric.align_to_liq(x_uni, y_uni, self.lower_price, self.upper_price, price)

#         vault.withdraw(x_uni_aligned, y_uni_aligned)

#         univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent, self.rebalance_cost)
#         univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)

#         portfolio.append(univ3_pos)
#         return None


# class BiCurrencyPassive(AbstractStrategy):
#     """
#     ``BiCurrencyPassive`` is the simplest strategy for asset pair.
#     This strategy only tracks own statistic in time
#         pool: UniswapV3 Pool instance
#         name: Unique name for the instance
#     """
#     def __init__(self,
#                  pool: Pool,
#                  name: str = None,
#                  ):
#         super().__init__(name)
#         self.decimal_diff = -pool.decimals_diff
#         self.fees_percent = pool.fee.percent

#     def rebalance(self, *args, **kwargs) -> bool:
#         timestamp = kwargs['timestamp']
#         row = kwargs['row']
#         portfolio = kwargs['portfolio']

#         price = row['price']

#         is_rebalanced = False

#         if 'Vault' not in portfolio.positions:
#             bicurrency = BiCurrencyPosition('Vault',
#                                             0.003,
#                                             0.01,
#                                             1 / price, 1,
#                                             0.0,
#                                             0.0)
#             portfolio.append(bicurrency)
#             is_rebalanced = True

#         return is_rebalanced




