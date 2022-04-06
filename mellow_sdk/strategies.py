from abc import ABC, abstractmethod
import numpy as np
import typing as tp
import copy

from mellow_sdk.uniswap_utils import UniswapLiquidityAligner
from mellow_sdk.positions import UniV3Position, BiCurrencyPosition
from mellow_sdk.primitives import Pool


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
    def rebalance(self, *args, **kwargs) -> tp.Optional[str]:
        """
        Rebalance implementation.

        Args:
            args: Any args.
            kwargs: Any kwargs.

        Returns:
            Name of event or None if there was no event.
        """
        raise Exception(NotImplemented)


class Hold(AbstractStrategy):
    """
        ``Hold`` is the passive strategy buy and hold.
    """
    def __init__(self, name: str = None):
        super().__init__(name)
        self.prev_gain_date = None

    def rebalance(self, *args, **kwargs):
        timestamp = kwargs['record']['timestamp']
        portfolio = kwargs['portfolio']

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.date()

        if timestamp.date() > self.prev_gain_date:
            vault = portfolio.get_position('Vault')
            vault.interest_gain(timestamp.date())
            self.prev_gain_date = timestamp.date()


class UniV3Passive(AbstractStrategy):
    """
    ``UniV3Passive`` is the passive strategy on UniswapV3, i.e. mint one interval and wait.

    Attributes:
        lower_price: Lower bound of the interval
        upper_price: Upper bound of the interval
        gas_cost: Gas costs, expressed in currency
        pool: UniswapV3 Pool instance
        name: Unique name for the instance
    """
    def __init__(self,
                 lower_price: float,
                 upper_price: float,
                 pool: Pool,
                 gas_cost: float,
                 name: str = None,
                 ):
        super().__init__(name)
        self.lower_price = lower_price
        self.upper_price = upper_price

        self.fee_percent = pool.fee.percent
        self.gas_cost = gas_cost
        self.swap_fee = pool.fee.percent

    def rebalance(self, *args, **kwargs) -> str:
        record = kwargs['record']
        portfolio = kwargs['portfolio']
        price_before, price = record['price_before'], record['price']

        is_rebalanced = None

        if len(portfolio.positions) == 0:
            self.create_uni_position(portfolio=portfolio, price=price)
            is_rebalanced = 'mint'

        if 'UniV3Passive' in portfolio.positions:
            uni_pos = portfolio.get_position('UniV3Passive')
            uni_pos.charge_fees(price_before, price)

        return is_rebalanced

    def create_uni_position(self, portfolio, price):
        x = 1 / price
        y = 1

        bi_cur = BiCurrencyPosition(
            name=f'main_vault',
            swap_fee=self.swap_fee,
            gas_cost=self.gas_cost,
            x=x,
            y=y,
            x_interest=None,
            y_interest=None
        )
        uni_pos = UniV3Position(
            name=f'UniV3Passive',
            lower_price=self.lower_price,
            upper_price=self.upper_price,
            fee_percent=self.fee_percent,
            gas_cost=self.gas_cost,
        )

        portfolio.append(bi_cur)
        portfolio.append(uni_pos)

        dx, dy = uni_pos.aligner.get_amounts_for_swap_to_optimal(
            x, y, swap_fee=bi_cur.swap_fee, price=price
        )

        if dx > 0:
            bi_cur.swap_x_to_y(dx, price=price)
        if dy > 0:
            bi_cur.swap_y_to_x(dy, price=price)

        x_uni, y_uni = uni_pos.aligner.get_amounts_after_optimal_swap(
            x, y, swap_fee=bi_cur.swap_fee, price=price
        )
        bi_cur.withdraw(x_uni, y_uni)
        uni_pos.deposit(x_uni, y_uni, price=price)


class StrategyByAddress(AbstractStrategy):
    """
    ``StrategyByAddress`` is the strategy on UniswapV3 that follows the actions of certain address.

    Attributes:
        address: The address to follow.
        pool: UniswapV3 Pool instance.
        gas_cost: Gas costs, expressed in currency.
        name: Unique name for the instance.
    """
    def __init__(self,
                 address: str,
                 pool: Pool,
                 gas_cost: float,
                 name: str = None,
                 ):
        super().__init__(name)

        self.address = address
        self.decimal_diff = -pool.decimals_diff
        self.fee_percent = pool.fee.percent
        self.gas_cost = gas_cost

    def rebalance(self, *args, **kwargs):
        is_rebalanced = None

        record = kwargs['record']
        portfolio = kwargs['portfolio']
        event = record['event']

        if event == 'mint':
            if record['owner'] == self.address:
                amount_0, amount_1, tick_lower, tick_upper, liquidity = (record['amount0'], record['amount1'],
                                                                         record['tick_lower'], record['tick_upper'],
                                                                         record['liquidity'])
                self.perform_mint(portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity)
                is_rebalanced = 'mint'

        if event == 'burn':
            if record['owner'] == self.address:
                amount_0, amount_1, tick_lower, tick_upper, liquidity, price = (
                    record['amount0'], record['amount1'],
                    record['tick_lower'], record['tick_upper'],
                    record['liquidity'], record['price']
                )
                self.perform_burn(portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity, price)
                is_rebalanced = 'burn'

        if event == 'swap':
            if record['owner'] == self.address:
                amount_0, amount_1 = record['amount0'], record['amount1']
                self.perform_swap(portfolio, amount_0, amount_1)
                is_rebalanced = 'swap'

        if event == 'swap':
            price_before, price = record['price_before'], record['price']
            for name, pos in portfolio.positions.items():
                if 'Uni' in name:
                    pos.charge_fees(price_before, price)

        self.perform_clearing(portfolio)
        return is_rebalanced

    def perform_swap(self, portfolio, amount_0, amount_1):
        vault = portfolio.get_position('Vault')
        if amount_0 > 0:
            if vault.x < amount_0:
                vault.deposit(amount_0 - vault.x + 1e-6, 0)
            vault.withdraw(amount_0, 0)
            vault.deposit(0, -amount_1)
        else:
            if vault.y < amount_1:
                vault.deposit(0, amount_1 - vault.y + 1e-6)
            vault.withdraw(0, amount_1)
            vault.deposit(-amount_0, 0)

    def perform_mint(self, portfolio, amount_0, amount_1, tick_lower, tick_upper, liquidity):
        name = f'UniV3_{tick_lower}_{tick_upper}'
        vault = portfolio.get_position('Vault')

        if vault.x < amount_0:
            vault.deposit(amount_0 - vault.x + 1e-6, 0)

        if vault.y < amount_1:
            vault.deposit(0, amount_1 - vault.y + 1e-6)

        x_uni, y_uni = vault.withdraw(amount_0, amount_1)

        price_lower, price_upper = self._tick_to_price(tick_lower), self._tick_to_price(tick_upper)

        if name in portfolio.positions:
            univ3_pos_old = portfolio.get_position(name)
            univ3_pos_old.liquidity = univ3_pos_old.liquidity + liquidity
            univ3_pos_old.x_hold += amount_0
            univ3_pos_old.y_hold += amount_1
            # univ3_pos_old.bi_currency.deposit(amount_0, amount_1)
        else:
            univ3_pos = UniV3Position(name, price_lower, price_upper, self.fee_percent, self.gas_cost)
            univ3_pos.liquidity = liquidity
            univ3_pos.x_hold += amount_0
            univ3_pos.y_hold += amount_1
            # univ3_pos.bi_currency.deposit(amount_0, amount_1)
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
                if univ3.liquidity < 1e1:
                    portfolio.remove(name)

    def _tick_to_price(self, tick):
        price = np.power(1.0001, tick)
        return price
