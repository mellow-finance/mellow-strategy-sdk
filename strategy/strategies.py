from strategy.uniswap_utils import UniswapV3Utils, UniswapV2Utils, UniswapLiquidityAligner
from strategy.positions import UniV3Position, BiCurrencyPosition
from strategy.primitives import Pool

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
    def rebalance(self, *args, **kwargs) -> str:
        """
        Rebalance implementation.

        Args:
            args: Any args.
            kwargs: Any kwargs.

        Returns:
            Name of event.
        """
        raise Exception(NotImplemented)


class Hold(AbstractStrategy):
    def __init__(self, name: str = None):
        super().__init__(name)
        self.prev_gain_date = None

    def rebalance(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.date()

        if timestamp.date() > self.prev_gain_date:
            vault = portfolio.get_position('Vault')
            vault.interest_gain(timestamp.date())
            self.prev_gain_date = timestamp.date()


class StrategyByAddress(AbstractStrategy):
    def __init__(self,
                 address,
                 pool_data,
                 pool: Pool,
                 rebalance_cost: float,
                 name: str = None,
                 ):
        super().__init__(name)

        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.rebalance_cost = rebalance_cost

        self.init_signals(pool_data, address)

    def init_signals(self, pool_data, address):
        self.swap_signal = pool_data.swaps.filter(pl.col('sender') == address)
        self.mint_signal = pool_data.mints.filter(pl.col('owner') == address)
        self.burn_signal = pool_data.burns.filter(pl.col('owner') == address)

    def rebalance(self, *args, **kwargs):
        # prepare data for strategy
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']
        row = kwargs['row']
        price_before, price = row['price_before'], row['price']

        block_current = row['block_number']
        log_current = row['log_index']

        current_tick = self._price_to_tick(price)

        is_rebalanced = None

        for name, pos in portfolio.positions.items():
            if 'Uni' in name:
                pos.charge_fees(price_before, price)
                # pos.reinvest_fees(price)

        # manage mint signal
        slice_mint_signal = self.mint_signal.filter(pl.col('block_number') <= block_current)
        self.mint_signal = self.mint_signal.filter(pl.col('block_number') > block_current)
        if slice_mint_signal.shape[0] > 0:
            for record in slice_mint_signal.to_dicts():
                amount_0, amount_1, tick_lower, tick_upper, liquidity = record['amount0'], record['amount1'], record[
                    'tick_lower'], record['tick_upper'], record['liquidity']
                self.perform_mint(portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity)
                is_rebalanced = 'mint'

        # manage swap signal
        slice_swap_signal = self.swap_signal.filter(pl.col('block_number') <= block_current)
        self.swap_signal = self.swap_signal.filter(pl.col('block_number') > block_current)
        if slice_swap_signal.shape[0] > 0:
            for record in slice_swap_signal.to_dicts():
                amount_0, amount_1, spot_price = record['amount0'], record['amount1'], record['price']
                self.perform_swap(portfolio, amount_0, amount_1, spot_price)
                is_rebalanced = 'swap'

        # manage burn signal
        slice_burn_signal = self.burn_signal.filter(pl.col('block_number') <= block_current)
        self.burn_signal = self.burn_signal.filter(pl.col('block_number') > block_current)
        if slice_burn_signal.shape[0] > 0:
            for record in slice_burn_signal.to_dicts():
                amount_0, amount_1, tick_lower, tick_upper, liquidity = record['amount0'], record['amount1'], record[
                    'tick_lower'], record['tick_upper'], record['liquidity']
                self.perform_burn(portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity, price)
                is_rebalanced = 'burn'

        self.perform_clearing(portfolio)
        return is_rebalanced

    def perform_swap(self, portfolio, amount_0, amount_1, price):
        vault = portfolio.get_position('Vault')
        if amount_0 > 0:
            if vault.x < amount_0:
                vault.deposit(amount_0 - vault.x, 0)
            vault.withdraw(amount_0, 0)
            vault.deposit(0, -amount_1)
        else:
            if vault.y < amount_1:
                vault.deposit(0, amount_1 - vault.y)
            vault.withdraw(0, amount_1)
            vault.deposit(-amount_0, 0)

    def perform_mint(self, portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity):
        name = f'UniV3_{tick_lower}_{tick_upper}'
        vault = portfolio.get_position('Vault')

        if vault.x < amount_0:
            vault.deposit(amount_0 - vault.x, 0)

        if vault.y < amount_1:
            vault.deposit(0, amount_1 - vault.y)

        x_uni, y_uni = vault.withdraw(amount_0, amount_1)

        price_lower, price_upper = self._tick_to_price(tick_lower), self._tick_to_price(tick_upper)

        if name in portfolio.positions:
            univ3_pos_old = portfolio.get_position(name)
            univ3_pos_old.liquidity = univ3_pos_old.liquidity + liquidity
            univ3_pos_old.bi_currency.deposit(amount_0, amount_1)
        else:
            univ3_pos = UniV3Position(name, price_lower, price_upper, self.fee_percent, self.rebalance_cost)
            univ3_pos.liquidity = liquidity
            univ3_pos.bi_currency.deposit(amount_0, amount_1)
            portfolio.append(univ3_pos)

    def perform_burn(self, portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity, price):
        name = f'UniV3_{tick_lower}_{tick_upper}'

        if name in portfolio.positions:
            univ3_pos_old = portfolio.get_position(name)
            vault = portfolio.get_position('Vault')
            vault.deposit(amount_0, amount_1)

            if liquidity > 0:
                if liquidity > univ3_pos_old.liquidity:
                    print('Diff =', liquidity - univ3_pos_old.liquidity)
                    x_out, y_out = univ3_pos_old.burn(univ3_pos_old.liquidity, price)
                else:
                    x_out, y_out = univ3_pos_old.burn(liquidity, price)
            else:
                print(f'Negative liq {liquidity}')
        else:
            print(f'There is no position to burn {name}')

    def perform_clearing(self, portfolio):
        poses = copy.copy(portfolio.positions)
        for name, pos in poses.items():
            if 'UniV3' in name:
                univ3 = portfolio.get_position(name)
                if univ3.liquidity < 1e3:
                    portfolio.remove(name)

    def _price_to_tick(self, price):
        tick = math.log(price, 1.0001) + self.decimal_diff * math.log(10, 1.0001)
        return int(round(tick))

    def _tick_to_price(self, tick):
        price = np.power(1.0001, tick) / 10 ** self.decimal_diff
        return price


class UniV3Passive(AbstractStrategy):
    """
    ``UniV3Passive`` is the passive strategy on UniswapV3 without rebalances.
        lower_price: Lower bound of the interval
        upper_price: Upper bound of the interval
        rebalance_cost: Rebalancing cost, expressed in currency
        pool: UniswapV3 Pool instance
        name: Unique name for the instance
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

    def rebalance(self, *args, **kwargs) -> str:
        timestamp = kwargs['timestamp']
        row = kwargs['row']
        portfolio = kwargs['portfolio']
        price_before, price = row['price_before'], row['price']

        is_rebalanced = None

        if len(portfolio.positions) == 0:
            univ3_pos = self.create_uni_position(price)
            portfolio.append(univ3_pos)
            is_rebalanced = 'mint'

        if 'UniV3Passive' in portfolio.positions:
            uni_pos = portfolio.get_position('UniV3Passive')
            uni_pos.charge_fees(price_before, price)

        return is_rebalanced

    def create_uni_position(self, price):
        univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent, self.rebalance_cost)
        x_uni_aligned, y_uni_aligned = univ3_pos.swap_to_optimal(x=1 / price, y=1, price=price)
        univ3_pos.deposit(x=x_uni_aligned, y=y_uni_aligned, price=price)
        return univ3_pos

