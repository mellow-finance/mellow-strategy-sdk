from strategy.uniswap_utils import UniswapLiquidityAligner
from strategy.positions import UniV3Position, BiCurrencyPosition
from strategy.primitives import Pool

from abc import ABC, abstractmethod
import math
import numpy as np
import typing as tp


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
        timestamp = kwargs['timestamp']
        portfolio = kwargs['portfolio']

        if self.prev_gain_date is None:
            self.prev_gain_date = timestamp.date()

        if timestamp.date() > self.prev_gain_date:
            vault = portfolio.get_position('Vault')
            vault.interest_gain(timestamp.date())
            self.prev_gain_date = timestamp.date()


class UniV3Passive(AbstractStrategy):
    """
    ``UniV3Passive`` is the passive strategy on UniswapV3 without rebalances.
        i.e. mint interval and wait.
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

