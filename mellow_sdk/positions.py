from typing import Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np

from mellow_sdk.uniswap_utils import UniswapLiquidityAligner


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
            New name for position.
        """
        self.name = new_name

    @abstractmethod
    def to_x(self, price: float) -> float:
        """
        Return amount of X and Y in vault expressed in X currency.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of vault expressed in X.
        """
        raise Exception(NotImplemented)

    @abstractmethod
    def to_y(self, price: float) -> float:
        """
        Return amount of X and Y in vault expressed in Y currency.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of vault expressed in Y.
        """
        raise Exception(NotImplemented)

    @abstractmethod
    def to_xy(self, price: float) -> Tuple[float, float]:
        """
        Get amount of X and amount of Y in vault.

        Args:
            price: Current price of X in Y currency.

        Returns:
            (amount of X, amount of Y)
        """
        raise Exception(NotImplemented)

    @abstractmethod
    def snapshot(self, timestamp: datetime, price: float) -> dict:
        """
        | Get a snapshot of the position. Used in ``Portfolio.snapshot`` to create a snapshot
        | of the entire portfolio when backtesting.

        Args:
            timestamp: Timestamp of snapshot.
            price: Current price of X in Y currency.

        Returns: Position snapshot.
        """
        raise Exception(NotImplemented)


class BiCurrencyPosition(AbstractPosition):
    """
    ``BiCurrencyPosition`` is a class corresponding to currency pair vault.

    Attributes:
        name: Unique name for the position.
        swap_fee: Exchange fee expressed as a percentage.
        gas_cost: Gas costs, expressed in Y currency.
        x: Amount of asset X.
        y: Amount of asset Y.
        x_interest: Interest on currency X deposit expressed as a daily percentage yield.
        y_interest: Interest on currency Y deposit expressed as a daily percentage yield.
   """
    def __init__(
        self,
        name: str,
        swap_fee: float,
        gas_cost: float,
        x: float = None,
        y: float = None,
        x_interest: float = None,
        y_interest: float = None,
    ) -> None:
        super().__init__(name)

        assert x >= 0, f'Can not init position with negative X = {x}'
        assert y >= 0, f'Can not init position with negative Y = {y}'

        self.x = x if x is not None else 0
        self.y = y if y is not None else 0

        self.x_interest = x_interest if x_interest is not None else 0
        self.y_interest = y_interest if y_interest is not None else 0

        self.swap_fee = swap_fee
        self.gas_cost = gas_cost
        self.total_gas_costs = 0
        self.previous_gain = None

    def deposit(self, x: float, y: float) -> None:
        """
        Deposit X currency and Y currency to position.

        Args:
            x: Value of X currency.
            y: Value of Y currency.
        """
        assert x >= 0, f'Can not deposit negative X = {x}'
        assert y >= 0, f'Can not deposit negative Y = {y}'

        self.x += x
        self.y += y

    def withdraw(self, x: float, y: float) -> Tuple[float, float]:
        """
        Withdraw x amount of X currency and y amount of Y currency from position.

        Args:
            x: Value of X currency.
            y: Value of Y currency.

        Returns:
             x amount withdrawn, y amount withdrawn.
        """
        assert x >= 0, f'Can not withdraw negative X = {x}'
        assert y >= 0, f'Can not withdraw negative Y = {y}'

        assert x <= self.x, f'Too much to withdraw X = {x} / {self.x}'
        assert y <= self.y, f'Too much to withdraw Y = {y} / {self.y}'
        self.x -= x
        self.y -= y

        return x, y

    def withdraw_fraction(self, fraction: float) -> Tuple[float, float]:
        """
        Withdraw percent of X currency and percent of Y currency from position.

        Args:
            fraction: Percent from 0 to 1.

        Returns:
             X amount withdrawn, Y amount withdrawn.
        """
        assert 0 <= fraction <= 1, f'Incorrect Fraction = {fraction}'
        x_out, y_out = self.withdraw(self.x * fraction, self.y * fraction)

        return x_out, y_out

    def rebalance(self, x_fraction: float, y_fraction: float, price: float) -> None:
        """
        Rebalance bi-currency vault with respect to their proportion.
        Note that the sum of x_fraction and y_fraction must be equal to 1.

        Args:
            x_fraction: Fraction of X after rebalance. from 0 to 1.
            y_fraction: Fraction of Y after rebalance. from 0 to 1.
            price: Current price of X in Y currency.
        """
        assert 0 <= x_fraction <= 1, f'Incorrect Fraction X = {x_fraction}'
        assert 0 <= y_fraction <= 1, f'Incorrect Fraction Y = {y_fraction}'
        assert self.x > 1e-6 or self.y > 1e-6, f'Cant rebalance empty portfolio x={self.x}, y={self.y}'
        assert abs(x_fraction + y_fraction - 1) <= 1e-6, f'Incorrect fractions {x_fraction}, {y_fraction}'
        d_v = y_fraction * price * self.x - x_fraction * self.y
        if d_v > 0:
            dx = d_v / price
            self.swap_x_to_y(dx, price)
        elif d_v < 0:
            dy = abs(d_v)
            self.swap_y_to_x(dy, price)

    def interest_gain(self, date: datetime) -> None:
        """
        Gain interest on deposit X, deposit Y.
        Note that you can only gain one time per day.

        Args:
            date: Gaining date.
        """
        if self.previous_gain is not None:
            assert self.previous_gain < date, "Already gained this day"
        else:
            self.previous_gain = date
        multiplier = (date - self.previous_gain).days
        self.x *= (1 + self.x_interest) ** multiplier
        self.y *= (1 + self.y_interest) ** multiplier
        self.previous_gain = date

    def to_x(self, price: float) -> float:
        """
        Return amount of X and Y in vault expressed in X currency.

        Args:
            price: Current price of X in Y currency

        Returns:
            Total value of vault expessed in X
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        res = self.x + self.y / price
        return res

    def to_y(self, price: float) -> float:
        """
        Return amount of X and Y in vault expressed in Y currency.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of vault expessed in Y.
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        res = self.x * price + self.y
        return res

    def to_xy(self, price: float) -> Tuple[float, float]:
        """
        Get amount of X and amount of Y in vault

        Args:
            price: Current price of X in Y currency.

        Returns:
            (amount of X, amount of Y)
        """
        return self.x, self.y

    def swap_x_to_y(self, dx: float, price: float) -> float:
        """
        Swap some X to Y.

        Args:
            dx: Amount of X to be swapped.
            price: Current price of X in Y currency.

        Returns:
            Amount of Y was got.
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        assert dx >= 0, f'Incorrect dX = {dx}'

        self.x -= dx
        dy = price * (1 - self.swap_fee) * dx
        self.y += dy
        self.total_gas_costs += self.gas_cost

        return dy

    def swap_y_to_x(self, dy: float, price: float) -> float:
        """
        Swap some Y to X.

        Args:
            dy: Amount of Y to be swapped.
            price: Current price of X in Y currency.

        Returns:
            Amount of X was got.
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        assert dy >= 0, f'Incorrect dY = {dy}'

        self.y -= dy
        dx = (1 - self.swap_fee) * dy / price
        self.x += dx
        self.total_gas_costs += self.gas_cost
        return dx

    def snapshot(self, timestamp: datetime, price: float) -> dict:
        """
        | Get a snapshot of the position. Used in ``Portfolio.snapshot`` to create a snapshot
        | of the entire portfolio when backtesting.

        Args:
            timestamp: Timestamp of snapshot.
            price: Current price of X in Y currency.

        Returns: Position snapshot.
        """
        snapshot = {
                f'{self.name}_value_x': float(self.x),
                f'{self.name}_value_y': float(self.y),
                f'{self.name}_total_gas_costs': float(self.total_gas_costs)
            }
        return snapshot


class UniV3Position(AbstractPosition):
    """
    ``UniV3Position`` is a class corresponding to one open UniswapV3 interval.
    It's defined by lower and upper bounds ``lower_price``, ``upper_price``
    and  pool fee percent ``fee_percent``.

    Attributes:
        name: Unique name for the position.
        lower_price: Lower bound of the interval (price).
        upper_price:  Upper bound of the interval (price).
        fee_percent: Amount of fee expressed as a percentage.
        gas_cost: Gas costs, expressed in Y currency.
   """
    def __init__(
        self,
        name: str,
        lower_price: float,
        upper_price: float,
        fee_percent: float,
        gas_cost: float,
    ) -> None:

        super().__init__(name)

        self.lower_price = lower_price
        self.upper_price = upper_price
        self.fee_percent = fee_percent
        self.gas_cost = gas_cost

        self.sqrt_lower = np.sqrt(self.lower_price)
        self.sqrt_upper = np.sqrt(self.upper_price)

        self.liquidity = 0

        self.x_hold = 0
        self.y_hold = 0

        self.total_gas_costs = 0

        self.realized_loss_to_x = 0
        self.realized_loss_to_y = 0

        self.fees_x = 0
        self._fees_x_earned_ = 0

        self.fees_y = 0
        self._fees_y_earned_ = 0

        self.aligner = UniswapLiquidityAligner(self.lower_price, self.upper_price)


    def deposit(self, x: float, y: float, price: float) -> None:
        """
        Deposit X and Y to position.

        Args:
            x: Value of X currency.
            y: Value of Y currency.
            price: Current price of X in Y currency.
        """

        assert x >= 0, f'Can not deposit negative X = {x}'
        assert y >= 0, f'Can not deposit negative Y = {y}'

        self.mint(x, y, price)

    def withdraw(self, price: float) -> Tuple[float, float]:
        """
        Withdraw all liquidity from UniswapV3 position.

        Args:
            price: Current price of X in Y currency.

        Returns:
            X amount withdrawn, Y amount withdrawn.
        """
        assert price > 1e-16, f'Incorrect Price = {price}'

        x_out, y_out = self.burn(self.liquidity, price)
        x_fees, y_fees = self.collect_fees()
        x_res, y_res = x_out + x_fees, y_out + y_fees

        return x_res, y_res

    def mint(self, x: float, y: float, price: float) -> None:
        """
        Mint X and Y to UniswapV3 interval.

        Args:
            x: Value of X currency.
            y: Value of Y currency.
            price: Current price of X in Y currency.
        """
        assert x >= 0, f'Can not mint negative X = {x}'
        assert y >= 0, f'Can not mint negative Y = {y}'
        assert price > 1e-16, f'Incorrect Price = {price}'

        is_optimal, x_liq, y_liq = self.aligner.check_xy_is_optimal(x=x, y=y, price=price)

        assert is_optimal, f"""
                    x={x}, y={y}, Lx={x_liq}, Ly={y_liq}, 
                    lower_price={self.lower_price}, upper_price={self.upper_price}, price={price}
                        if price <= lower_price:
                            must be y=0
                        if price >= upper_price:
                            must be x=0
                        if lower_price < price <  upper_price:
                            must be Lx=Ly
                """

        d_liq = self.aligner.xy_to_liq(x=x, y=y, price=price)

        self.liquidity += d_liq
        self.x_hold += x
        self.y_hold += y
        self.total_gas_costs += self.gas_cost

    def burn(self, liq: float, price: float) -> Tuple[float, float]:
        """
        Burn some liquidity from UniswapV3 position.

        Args:
            liq: Value of liquidity to burn.
            price: Current price of X in Y currency.

        Returns:
            (X received after burn, Y received after burn).
        """
        assert liq <= self.liquidity, f'Too much liquidity too withdraw = {liq} / {self.liquidity}'
        assert liq > 1e-16, f'Too small liquidity too withdraw = {liq}'
        assert price > 1e-16, f'Incorrect Price = {price}'

        il_x_0 = self.impermanent_loss_to_x(price)
        il_y_0 = self.impermanent_loss_to_y(price)

        x_out, y_out = self.aligner.liq_to_xy(price=price, liq=liq)

        self.x_hold -= self.x_hold * (liq / self.liquidity)
        self.y_hold -= self.y_hold * (liq / self.liquidity)

        self.liquidity -= liq

        il_x_1 = self.impermanent_loss_to_x(price)
        il_y_1 = self.impermanent_loss_to_y(price)

        self.realized_loss_to_x += (il_x_0 - il_x_1)
        self.realized_loss_to_y += (il_y_0 - il_y_1)

        self.total_gas_costs += self.gas_cost

        return x_out, y_out

    def charge_fees(self, price_0: float, price_1: float) -> None:
        """
        Charge fees for swap.

        Args:
            price_0: Price before swap.
            price_1: Price after swap.
        """

        # TODO: research how to charge fees in better way (check UniV3 docs)
        assert price_0 > 1e-16, f'Incorrect Price = {price_0}'
        assert price_1 > 1e-16, f'Incorrect Price = {price_1}'

        x_0, y_0 = self.to_xy(price_0)
        x_1, y_1 = self.to_xy(price_1)

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

    # def reinvest_fees(self, price) -> None:
    #     """
    #     Collect all gained fees and reinvest to current position.
    #
    #     Args:
    #         price: Current price of X in Y currency.
    #     """
    #     assert price > 1e-16, f'Incorrect Price = {price}'
    #
    #     fees_x, fees_y = self.collect_fees()
    #     self.mint(fees_x, fees_y, price)
    #     return None

    def impermanent_loss(self, price: float) -> Tuple[float, float]:
        """
        Calculate impermanent loss separately in X and Y currencies.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Value of X il, value of Y il.
        """
        assert price > 1e-16, f'Incorrect Price = {price}'

        x_stake, y_stake = self.to_xy(price)
        il_x = self.x_hold - x_stake
        il_y = self.y_hold - y_stake
        return il_x, il_y

    def impermanent_loss_to_x(self, price: float) -> float:
        """
        Calculate impermanent loss denominated in X.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Value of X il.
        """
        assert price > 1e-16, f'Incorrect Price = {price}'
        v_hold = self.x_hold + self.y_hold / price
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
        assert price > 1e-16, f'Incorrect Price = {price}'

        v_hold = self.x_hold * price + self.y_hold
        v_stake = self.to_y(price)
        il_y = v_hold - v_stake
        return il_y

    def to_x(self, price: float) -> float:
        """
        Get value of UniswapV3 position expressed in X.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of UniswapV3 position expressed in X.
        """
        assert price > 1e-16, f'Incorrect Price = {price}'

        x, y = self.to_xy(price)
        value_x = x + y / price
        return value_x

    def to_y(self, price: float) -> float:
        """
        Get value of UniswapV3 position expressed in Y.

        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of UniswapV3 position expressed in Y.
        """
        assert price > 1e-16, f'Incorrect Price = {price}'

        x, y = self.to_xy(price)
        value_y = x * price + y
        return value_y

    def to_xy(self, price) -> Tuple[float, float]:
        """
        Get amount of X and amount of Y in position.

        Args:
            price: Current price of X in Y currency.

        Returns:
            amount of X and amount of Y in position.
        """
        assert price > 1e-16, f'Incorrect Price = {price}'

        x, y = self.aligner.liq_to_xy(price=price, liq=self.liquidity)

        return x, y

    def snapshot(self, timestamp: datetime, price: float) -> dict:
        """
        | Get a snapshot of the position. Used in ``Portfolio.snapshot`` to create a snapshot
        | of the entire portfolio when backtesting.

        Args:
            timestamp: Timestamp of snapshot
            price: Current price of X in Y currency

        Returns: Position snapshot
        """
        x, y = self.to_xy(price)
        il_to_x, il_to_y = self.impermanent_loss_to_x(price), self.impermanent_loss_to_y(price)

        snapshot = {
            f'{self.name}_value_x': float(x + self.fees_x),
            f'{self.name}_value_y': float(y + self.fees_y),

            f'{self.name}_fees_x': float(self.fees_x),
            f'{self.name}_fees_y': float(self.fees_y),

            f'{self.name}_il_to_x': float(il_to_x),
            f'{self.name}_il_to_y': float(il_to_y),

            f'{self.name}_total_gas_costs': float(self.total_gas_costs),

            # f'{self.name}_current_liquidity': self.liquidity
        }
        return snapshot
