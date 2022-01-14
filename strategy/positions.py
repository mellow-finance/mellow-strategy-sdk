from typing import Tuple
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime


class AbstractPosition(ABC):
    """
    ``AbstractPosition`` is an abstract class for Position and Portfolio classes.

    Attributes:
        name: Unique name for the position.
    """
    def __init__(self, name: str) -> None:
        self.name = name
    
    def rename(self, new_name: str) -> None:
        """
        Rename position.

        Args:
            new_name: New name for position.
        """
        self.name = new_name

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
    def snapshot(self, timestamp: datetime, price: float) -> dict:
        raise Exception(NotImplemented)


class BiCurrencyPosition(AbstractPosition):
    """
        ``BiCurrencyPosition`` is a class corresponding to currency pair.
        Attributes:

            name: Unique name for the position.
            swap_fee: Exchange fee expressed as a percentage.
            rebalance_cost: Rebalancing cost, expressed in Y currency.
            x: Amount of asset X.
            y: Amount of asset Y.
            x_interest: Interest on currency X deposit expressed as a daily percentage yield.
            y_interest: Interest on currency Y deposit expressed as a daily percentage yield.
   """

    def __init__(self, name: str,
                 swap_fee: float,
                 rebalance_cost: float,
                 x: float = None,
                 y: float = None,
                 x_interest: float = None,
                 y_interest: float = None,
                 ) -> None:
        super().__init__(name)

        self.x = x if x is not None else 0
        self.y = y if y is not None else 0

        self.x_interest = x_interest if x_interest is not None else 0
        self.y_interest = y_interest if y_interest is not None else 0

        self.swap_fee = swap_fee
        self.rebalance_cost = rebalance_cost
        self.rebalance_costs_to_x = 0
        self.rebalance_costs_to_y = 0
        self.previous_gain = None

    def deposit(self, x: float, y: float) -> None:
        """
        Deposit X currency and Y currency to position.

        Args:
            x: Value of X currency
            y: Value of Y currency
        """
        self.x += x
        self.y += y
        return None

    def withdraw(self, x: float, y: float) -> Tuple[float, float]:
        """
        Withdraw X currency and Y currency from position

        Args:
            x: Value of X currency
            y: Value of Y currency

        Returns:
             Value of X, value of Y
        """
        assert x <= self.x, f'Too much to withdraw X = {x}'
        assert y <= self.y, f'Too much to withdraw Y = {y}'
        self.x -= x
        self.y -= y
        return x, y

    def withdraw_fraction(self, fraction: float) -> Tuple[float, float]:
        """
        Withdraw percent of X currency and percent of Y currency from position

        Args:
            fraction: Fraction from 0 to 1.

        Returns:
             Fraction of current X and Y.
        """
        assert fraction <= 1, f'Too much to withdraw Fraction = {fraction}'
        x_out, y_out = self.withdraw(self.x * fraction, self.y * fraction)
        return x_out, y_out

    def rebalance(self, x_fraction: float, y_fraction: float, price: float) -> None:
        """
        Rebalance bicurrency pair with respect to their proportion.

        Args:
            x_fraction: Fraction of X after rebalance from 0 to 1.
            y_fraction: Fraction of Y after rebalance from 0 to 1.
            price: Current price of X in Y currency.
        """
        assert x_fraction <= 1, f'Too much to rebalance Fraction X = {x_fraction}'
        assert y_fraction <= 1, f'Too much to rebalance Fraction Y = {y_fraction}'
        assert abs(x_fraction + y_fraction - 1) <= 1e-6, f'Incorrect fractions {x_fraction}, {y_fraction}'

        d_v = y_fraction * price * self.x - x_fraction * self.y
        if d_v > 0:
            dx = d_v / price
            self.swap_x_to_y(dx, price)
        elif d_v < 0:
            dy = abs(d_v)
            self.swap_y_to_x(dy, price)

        self.rebalance_costs_to_x += self.rebalance_cost / price
        self.rebalance_costs_to_y += self.rebalance_cost

        return None

    def interest_gain(self, date) -> None:
        """
        Gain deposit interest.

        Args:
            date: Gaining date.
        """
        if self.previous_gain is not None:
            assert self.previous_gain < date, "Already gained this day"
        else:
            self.previous_gain = date
        multiplier = (date - self.previous_gain).days
        self.x *= (1 + self.x_interest) ** multiplier
        self.y *= (1 + self.x_interest) ** multiplier
        self.previous_gain = date
        return None

    def to_x(self, price: float) -> float:
        """
        Get total value of position expessed in X.

        Args:
            price: Current price of X in Y currency

        Returns:
            Total value of position expessed in X
        """
        res = self.x + self.y / price
        return res

    def to_y(self, price: float) -> float:
        """
        Get total value of position expessed in Y.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of position expessed in Y.
        """
        res = self.x * price + self.y
        return res

    def to_xy(self, price: float) -> Tuple[float, float]:
        """
        Get values of bicurrency pair.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Position value to X and Y.
        """
        return self.x, self.y

    def swap_x_to_y(self, dx: float, price: float) -> None:
        """
        Swap X currency to Y.

        Args:
            dx: Amount of X to be swapped.
            price: Current price of X in Y currency.
        """
        self.x -= dx
        self.y += price * (1 - self.swap_fee) * dx
        self.rebalance_costs_to_x += self.rebalance_cost / price
        self.rebalance_costs_to_y += self.rebalance_cost
        return None

    def swap_y_to_x(self, dy: float, price: float) -> None:
        """
        Swap Y currency to X.

        Args:
            dy: Amount of X to be swapped.
            price: Current price of X in Y currency.
        """
        self.y -= dy
        self.x += (1 - self.swap_fee) * dy / price
        self.rebalance_costs_to_x += self.rebalance_cost / price
        self.rebalance_costs_to_y += self.rebalance_cost
        return None

    def snapshot(self, timestamp: datetime, price: float) -> dict:
        """
        Get position snapshot.

        Args:
            timestamp: Timestamp of snapshot
            price: Current price of X in Y currency

        Returns: Position snapshot
        """
        value_to_x = self.to_x(price)
        value_to_y = self.to_y(price)
        snapshot = {
                    f'{self.name}_value_to_x': value_to_x,
                    f'{self.name}_value_to_y': value_to_y,
                    f'{self.name}_rebalance_costs_to_x': self.rebalance_costs_to_x,
                    f'{self.name}_rebalance_costs_to_y': self.rebalance_costs_to_y,
                }
        return snapshot


class UniV3Position(AbstractPosition):
    """
        ``UniV3Position`` is a class corresponding to one investment into UniswapV3 interval.
        It's defined by lower and upper bounds ``lower_price``, ``upper_price`` and  pool fee percent ``fee_percent``.

        Attributes:
            name: Unique name for the position
            lower_price: Lower bound of the interval (price)
            upper_price:  Upper bound of the interval (price)
            fee_percent: Amount of fee expressed as a percentage
            rebalance_cost: Rebalancing cost, expressed in currency
   """
    def __init__(self,
                 name: str,
                 lower_price: float,
                 upper_price: float,
                 fee_percent: float,
                 rebalance_cost: float,
                 ) -> None:

        super().__init__(name)

        self.lower_price = lower_price
        self.upper_price = upper_price
        self.fee_percent = fee_percent
        self.rebalance_cost = rebalance_cost

        self.sqrt_lower = np.sqrt(self.lower_price)
        self.sqrt_upper = np.sqrt(self.upper_price)

        self.liquidity = 0
        self.bi_currency = BiCurrencyPosition('Virtual', self.fee_percent, self.rebalance_cost)
        self.rebalance_costs_to_x = 0
        self.rebalance_costs_to_y = 0

        self.realized_loss_to_x = 0
        self.realized_loss_to_y = 0

        self.fees_x = 0
        self._fees_x_earned_ = 0

        self.fees_y = 0
        self._fees_y_earned_ = 0

    def deposit(self, x: float, y: float, price: float) -> None:
        """
        Deposit X and Y to position.

        Args:
            x: Value of X currency.
            y: Value of Y currency.
            price: Current price of X in Y currency.
        """
        self.mint(x, y, price)
        return None

    def withdraw(self, price: float) -> Tuple[float, float]:
        """
        Withdraw all liquidity from UniswapV3 position.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Value of X, value of Y.
        """
        x_out, y_out = self.burn(self.liquidity, price)
        x_fees, y_fees = self.collect_fees()
        x_res, y_res = x_out + x_fees, y_out + y_fees
        return x_res, y_res

    def mint(self, x: float, y: float, price: float) -> None:
        """
        Mint X and Y to uniswapV3 interval.

        Args:
            x: Value of X currency.
            y: Value of Y currency.
            price:
            Current price of X in Y currency.
        """
        d_liq = self._xy_to_liq_(x, y, price)
        self.liquidity += d_liq
        self.bi_currency.deposit(x, y)
        self.rebalance_costs_to_x += self.rebalance_cost / price
        self.rebalance_costs_to_y += self.rebalance_cost
        return None

    def burn(self, liq: float, price: float) -> Tuple[float, float]:
        """
        Burn liquidity from uniswapV3 interval.

        Args:
            liq: Value of liquidity.
            price: Current price of X in Y currency.

        Returns: Value of X, value of Y.
        """
        assert liq <= self.liquidity, f'Too much liquidity too withdraw = {liq}'
        assert liq > 1e-6, f'Too small liquidity too withdraw = {liq}'
        il_x_0 = self.impermanent_loss_to_x(price)
        il_y_0 = self.impermanent_loss_to_y(price)

        x_out, y_out = self._liq_to_xy_(liq, price)

        self.bi_currency.withdraw_fraction(liq / self.liquidity)
        self.liquidity -= liq

        il_x_1 = self.impermanent_loss_to_x(price)
        il_y_1 = self.impermanent_loss_to_y(price)

        self.realized_loss_to_x += (il_x_0 - il_x_1)
        self.realized_loss_to_y += (il_y_0 - il_y_1)
        self.rebalance_costs_to_x += self.rebalance_cost / price
        self.rebalance_costs_to_y += self.rebalance_cost
        return x_out, y_out

    def charge_fees(self, price_0: float, price_1: float) -> None:
        """
        Charge exchange fees.

        Args:
            price_0: Price before exchange.
            price_1: Price after exchange.
        """
        price_0_adj = self._adj_price_(price_0)
        price_1_adj = self._adj_price_(price_1)

        x_0, y_0 = self.to_xy(price_0_adj)
        x_1, y_1 = self.to_xy(price_1_adj)

        fee_x, fee_y = 0, 0
        if y_0 >= y_1:
            fee_x = (x_1 - x_0) * self.fee_percent
            if fee_x < 0:
                raise Exception(f'Negative X fees earned: {fee_x}')
        else:
            fee_y = (y_1 - y_0) * self.fee_percent
            if fee_y < 0:
                raise Exception(f'Negative Y fees earned: {fee_y}')

        self.fees_x += fee_x
        self._fees_x_earned_ += fee_x

        self.fees_y += fee_y
        self._fees_y_earned_ += fee_y
        return None

    def collect_fees(self) -> Tuple[float, float]:
        """
        Collect all gained fees.

        Returns:
            Value of X fees, value of Y fees.
        """
        fees_x = self.fees_x
        fees_y = self.fees_y
        self.fees_x = 0
        self.fees_y = 0
        return fees_x, fees_y

    def reinvest_fees(self, price) -> None:
        """
        Collect all gained fees and reinvest to current position.

        Args:
            price: Current price of X in Y currency.
        """
        fees_x, fees_y = self.collect_fees()
        self.mint(fees_x, fees_y, price)
        return None

    def impermanent_loss(self, price: float) -> Tuple[float, float]:
        """
        Calculate impermanent loss separately in X and Y currencies.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Value of X il, value of Y il.
        """
        x_hold, y_hold = self.bi_currency.to_xy(price)
        x_stake, y_stake = self.to_xy(price)
        il_x = x_hold - x_stake
        il_y = y_hold - y_stake
        return il_x, il_y

    def impermanent_loss_to_x(self, price: float) -> float:
        """
        Calculate impermanent loss denominated in X.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Value of X il.
        """
        v_hold = self.bi_currency.to_x(price)
        v_stake = self.to_x(price)
        il_x = v_hold - v_stake
        return il_x

    def impermanent_loss_to_y(self, price: float) -> float:
        """
        Calculate impermanent loss denominated in Y.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Value of Y il.
        """
        v_hold = self.bi_currency.to_y(price)
        v_stake = self.to_y(price)
        il_y = v_hold - v_stake
        return il_y

    def to_x(self, price: float) -> float:
        """
        Get value of UniswapV3 position expessed in X.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of uniswapV3 position expessed in X.
        """
        x, y = self.to_xy(price)
        vol_x = x + y / price
        return vol_x

    def to_y(self, price: float) -> float:
        """
        Get value of UniswapV3 position expessed in Y.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of UniswapV3 position expessed in Y.
        """
        x, y = self.to_xy(price)
        vol_y = x * price + y
        return vol_y

    def to_xy(self, price) -> Tuple[float, float]:
        """
        Get values of position in X and Y.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Position value to X and Y.
        """
        x, y = self._liq_to_xy_(self.liquidity, price)
        return x, y

    def _adj_price_(self, price: float) -> float:
        """
        Get adjusted price of current price and UniswapV3 interval boundaries.

        Args:
            price: current price of X in Y currency.

        Returns:
            Adjusted price.
        """
        adj_price = min(max(self.lower_price, price), self.upper_price)
        return adj_price

    def _x_to_liq_(self, x: float, price: float) -> float:
        """
        Transform X to liquidity.

        Args:
            x: Value of X.
            price: Current price of X in Y currency.

        Returns:
            Resulting liquidity.
        """
        if self.upper_price <= price:
            return np.inf
        sqrt_price = np.sqrt(price)
        l_x = (x * sqrt_price * self.sqrt_upper) / (self.sqrt_upper - sqrt_price)
        return l_x

    def _y_to_liq_(self, y: float, price: float) -> float:
        """
        Transform Y to liquidity.

        Args:
            y: Value of Y.
            price: Current price of X in Y currency.

        Returns:
            Resulting liquidity.
        """
        if self.lower_price >= price:
            return np.inf
        sqrt_price = np.sqrt(price)
        l_y = y / (sqrt_price - self.sqrt_lower)
        return l_y

    def _xy_to_liq_(self, x: float, y: float, price: float) -> float:
        """
        Transform X and Y to liquidity.

        Args:
            x: Value of X.
            y: Value of Y.
            price: Current price of X in Y currency.

        Returns:
            Resulting liquidity.
        """
        adj_price = self._adj_price_(price)
        x_liq = self._x_to_liq_(x, adj_price)
        y_liq = self._y_to_liq_(y, adj_price)
        assert (x_liq >= 0) & (y_liq >= 0), f'Lx or Ly less then 0: Lx={x_liq}, Ly={y_liq}'
        if np.isinf(x_liq):
            return y_liq
        elif np.isinf(y_liq):
            return x_liq
        assert abs(x_liq - y_liq) < 1e-6, f'Lx != Ly: Lx={x_liq}, Ly={y_liq}'
        liq = min(x_liq, y_liq)
        return liq

    def _liq_to_x_(self, liq: float, price: float) -> float:
        """
        Transform liquidity to X.

        Args:
            liq: Value of liq.
            price: Current price of X in Y currency.

        Returns:
            Value of X.
        """
        adj_price = self._adj_price_(price)
        sqrt_price = np.sqrt(adj_price)
        numer = self.sqrt_upper - sqrt_price
        denom = self.sqrt_upper * sqrt_price
        x = liq * numer / denom
        return x

    def _liq_to_y_(self, liq: float, price: float) -> float:
        """
        Transform liquidity to Y.

        Args:
            liq: Value of liq.
            price: Current price of X in Y currency.

        Returns:
            Value of Y.
        """
        adj_price = self._adj_price_(price)
        sqrt_price = np.sqrt(adj_price)
        y = liq * (sqrt_price - self.sqrt_lower)
        return y

    def _liq_to_xy_(self, liq: float, price: float) -> Tuple[float, float]:
        """
        Transform liquidity to X, Y pair.

        Args:
            liq: Value of liq.
            price: Current price of X in Y currency.

        Returns:
            Value of X and Y.
        """
        x = self._liq_to_x_(liq, price)
        y = self._liq_to_y_(liq, price)
        return x, y

    def snapshot(self, timestamp: datetime, price: float) -> dict:
        """
        Get uniswapV3 position snapshot.

        Args:
            timestamp: timestamp of snapshot.
            price: Current price of X in Y currency.

        Returns:
            UniswapV3 position snapshot.
        """
        volume_to_x = self.to_x(price)
        volume_to_y = self.to_y(price)

        fees_earned_to_x = self._fees_x_earned_ + self._fees_y_earned_ / price
        fees_earned_to_y = price * self._fees_x_earned_ + self._fees_y_earned_

        fees_to_x = self.fees_x + self.fees_y / price
        fees_to_y = price * self.fees_x + self.fees_y

        il_to_x = self.impermanent_loss_to_x(price)
        il_to_y = self.impermanent_loss_to_y(price)
        
        current_liquidity = self.liquidity

        snapshot = {f'{self.name}_value_to_x': volume_to_x,
                    f'{self.name}_value_to_y': volume_to_y,

                    f'{self.name}_earned_fees_to_x': fees_earned_to_x,
                    f'{self.name}_earned_fees_to_y': fees_earned_to_y,

                    f'{self.name}_current_fees_to_x': fees_to_x,
                    f'{self.name}_current_fees_to_y': fees_to_y,

                    f'{self.name}_il_to_x': il_to_x,
                    f'{self.name}_il_to_y': il_to_y,

                    f'{self.name}_realized_loss_to_x': self.realized_loss_to_x,
                    f'{self.name}_realized_loss_to_y': self.realized_loss_to_y,

                    f'{self.name}_rebalance_costs_to_x': self.rebalance_costs_to_x,
                    f'{self.name}_rebalance_costs_to_y': self.rebalance_costs_to_y,
                    
                    f'{self.name}_current_liquidity': current_liquidity
                    }
        return snapshot
