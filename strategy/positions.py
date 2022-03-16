from typing import Tuple
from abc import ABC, abstractmethod
from datetime import datetime

import numpy as np
from strategy.uniswap_utils import UniswapLiquidityAligner


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
        Args:
            price: Current price of X in Y currency

        Returns:
            Total value of vault expessed in X
        """
        raise Exception(NotImplemented)

    @abstractmethod
    def to_y(self, price: float) -> float:
        """
        Args:
            price: Current price of X in Y currency.

        Returns:
            Total value of vault expessed in Y.
        """
        raise Exception(NotImplemented)

    @abstractmethod
    def to_xy(self, price: float) -> Tuple[float, float]:
        """
        Get amount of X and amount of Y in vault

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
        | for linking in the backtest metrics, you can to add metrics here

        Args:
            timestamp: Timestamp of snapshot
            price: Current price of X in Y currency

        Returns: Position snapshot
        """
        raise Exception(NotImplemented)


class BiCurrencyPosition(AbstractPosition):
    """
    ``BiCurrencyPosition`` is a class corresponding to currency pair vault.

    Attributes:
        name: Unique name for the position.
        swap_fee: Exchange fee expressed as a percentage.
        rebalance_cost: Rebalancing cost, expressed in Y currency.
        x: Amount of asset X.
        y: Amount of asset Y.
        x_interest: Interest on currency X deposit expressed as a daily percentage yield.
        y_interest: Interest on currency Y deposit expressed as a daily percentage yield.
   """
    def __init__(self,
                 name: str,
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
        self.total_rebalance_costs = 0
        self.previous_gain = None

    def deposit(self, x: float, y: float) -> None:
        """
        Deposit X currency and Y currency to position.

        Args:
            x: Value of X currency
            y: Value of Y currency
        """
        assert x >= 0, f'Can not deposit negative X = {x}'
        assert y >= 0, f'Can not deposit negative Y = {y}'
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
             X amount withdrawn, Y amount withdrawn
        """
        assert x <= self.x, f'Too much to withdraw X = {x} / {self.x}'
        assert y <= self.y, f'Too much to withdraw Y = {y} / {self.y}'
        self.x -= x
        self.y -= y
        return x, y

    def withdraw_fraction(self, fraction: float) -> Tuple[float, float]:
        """
        Withdraw percent of X currency and percent of Y currency from position

        Args:
            fraction: Fraction from 0 to 1.

        Returns:
             X amount withdrawn, Y amount withdrawn
        """
        assert 0 <= fraction <= 1, f'Incorrect Fraction = {fraction}'
        x_out, y_out = self.withdraw(self.x * fraction, self.y * fraction)
        return x_out, y_out

    def rebalance(self, x_fraction: float, y_fraction: float, price: float) -> None:
        """
        Rebalance bicurrency vault with respect to their proportion.

        Args:
            x_fraction: Fraction of X after rebalance. from 0 to 1.
            y_fraction: Fraction of Y after rebalance. from 0 to 1.
            price: Current price of X in Y currency.
        """
        assert 0 <= x_fraction <= 1, f'Incorrect Fraction X = {x_fraction}'
        assert 0 <= y_fraction <= 1, f'Incorrect Fraction Y = {y_fraction}'
        assert self.x > 1e-6 or self.y > 1e-6, f'Cant rebalance empty portfolio x={self.x}, y={self.y}'
        assert abs(x_fraction + y_fraction - 1) <= 1e-6, \
            f'Incorrect fractions {x_fraction}, {y_fraction}'
        d_v = y_fraction * price * self.x - x_fraction * self.y
        if d_v > 0:
            dx = d_v / price
            self.swap_x_to_y(dx, price)
        elif d_v < 0:
            dy = abs(d_v)
            self.swap_y_to_x(dy, price)

    def interest_gain(self, date: datetime) -> None:
        """
        Get interest on deposit X, deposit Y

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
            Amount of Y was getted
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        assert dx >= 0, f'Incorrect dX = {dx}'

        self.x -= dx
        dy = price * (1 - self.swap_fee) * dx
        self.y += dy
        self.total_rebalance_costs += self.rebalance_cost

        return dy

    def swap_y_to_x(self, dy: float, price: float) -> float:
        """
        Swap some Y to X.

        Args:
            dy: Amount of Y to be swapped.
            price: Current price of X in Y currency.
        Returns:
            Amount of X was getted
        """
        assert price > 1e-16, f'Incorrect price = {price}'
        assert dy >= 0, f'Incorrect dY = {dy}'

        self.y -= dy
        dx = (1 - self.swap_fee) * dy / price
        self.x += dx
        self.total_rebalance_costs += self.rebalance_cost
        return dx

    def snapshot(self, timestamp: datetime, price: float) -> dict:
        """
        | Get a snapshot of the position. Used in ``Portfolio.snapshot`` to create a snapshot
        of the entire portfolio when backtesting.
        | for linking in the backtest metrics, you can to add metrics here

        Args:
            timestamp: Timestamp of snapshot
            price: Current price of X in Y currency

        Returns: Position snapshot
        """
        snapshot = {
                f'{self.name}_value_x': float(self.x),
                f'{self.name}_value_y': float(self.y),
                # f'{self.name}total_rebalance_costs': self.total_rebalance_costs,
            }
        return snapshot


class UniV3Position(AbstractPosition):
    """
    ``UniV3Position`` is a class corresponding to one open UniswapV3 interval.
    It's defined by lower and upper bounds ``lower_price``, ``upper_price``
    and  pool fee percent ``fee_percent``.

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
        self.total_rebalance_costs = 0

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
        self.mint(x, y, price)

    def withdraw(self, price: float) -> Tuple[float, float]:
        """
        Withdraw all liquidity from UniswapV3 position.

        Args:
            price: Current price of X in Y currency.

        Returns:
            X amount withdrawn, Y amount withdrawn
        """
        assert price > 1e-16, f'Incorrect Price = {price}'

        x_out, y_out = self.burn(self.liquidity, price)
        x_fees, y_fees = self.collect_fees()
        x_res, y_res = x_out + x_fees, y_out + y_fees
        return x_res, y_res

    def swap_to_optimal(self, x: float, y: float, price: float) -> Tuple[float, float]:
        """
        For price and amounts perform swap to token amounts that can be completely mint.

        Args:
            x: number of tokens X
            y: number of tokens X
            price: current market price

        Returns:
            (optimal number of tokens X, optimal number of tokens Y)
        """
        sqrt_price = np.sqrt(price)
        sqrt_lower = np.sqrt(self.lower_price)
        sqrt_upper = np.sqrt(self.upper_price)

        if self.aligner.check_xy_is_optimal(x=x, y=y, price=price)[0]:
            return x, y

        if price <= self.lower_price:
            dx = self._swap_y_to_x(dy=y, price=price)
            return x + dx, 0

        if price >= self.upper_price:
            dy = self._swap_x_to_y(dx=x, price=price)
            return 0, y + dy

        price_real = (sqrt_price - sqrt_lower) * sqrt_upper * sqrt_price / (sqrt_upper - sqrt_price)

        v_y = price * x + y
        x_new = v_y / (price + price_real)
        y_new = price_real * x_new

        if x_new < x:
            self._swap_x_to_y(dx=x - x_new, price=price)
        else:
            self._swap_y_to_x(dy=y - y_new, price=price)

        return x_new, y_new

    def _swap_x_to_y(self, dx, price) -> float:
        """
        Using ``BiCurrencyPosition`` vault swap x tokens to y tokens.
        Args:
            dx: Amount of X to be swapped.
            price: Current price of X in Y currency.

        Returns:
            Amount of Y was getted
        """

        self.bi_currency.deposit(x=dx, y=0)
        dy = self.bi_currency.swap_x_to_y(dx=dx, price=price)
        self.bi_currency.y -= dy
        return dy

    def _swap_y_to_x(self, dy, price) -> float:
        """
        Args:
            dy: Amount of Y to be swapped.
            price: Current price of X in Y currency.
        Returns:
            Amount of X was getted
        """
        self.bi_currency.deposit(x=0, y=dy)
        dx = self.bi_currency.swap_y_to_x(dy=dy, price=price)
        self.bi_currency.x -= dx
        return dx

    def mint(self, x: float, y: float, price: float) -> None:
        """
        Mint X and Y to uniswapV3 interval.

        Args:
            x: Value of X currency.
            y: Value of Y currency.
            price: Current price of X in Y currency.
        """
        assert x >= 0, f'Can not deposit negative X = {x}'
        assert y >= 0, f'Can not deposit negative Y = {y}'
        assert price > 1e-16, f'Incorrect Price = {price}'

        is_optimal, x_liq, y_liq = self.aligner.check_xy_is_optimal(x=x, y=y, price=price)

        assert is_optimal, f"""
                    x={x}, y={y}, Lx={x_liq}, Ly={y_liq}, lower_price={self.lower_price},
                    upper_price={self.lower_price}, price={price}
                        if price <= lower_price:
                            must be y=0
                        if price >= upper_price:
                            must be x=0
                        if lower_price < price <  upper_price:
                            must be Lx=Ly
                """

        d_liq = self.aligner.xy_to_liq(x=x, y=y, price=price)

        self.liquidity += d_liq
        self.bi_currency.deposit(x, y)
        self.total_rebalance_costs += self.rebalance_cost

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

        self.bi_currency.withdraw_fraction(liq / self.liquidity)
        self.liquidity -= liq

        il_x_1 = self.impermanent_loss_to_x(price)
        il_y_1 = self.impermanent_loss_to_y(price)

        self.realized_loss_to_x += (il_x_0 - il_x_1)
        self.realized_loss_to_y += (il_y_0 - il_y_1)

        self.total_rebalance_costs += self.rebalance_cost

        return x_out, y_out

    def charge_fees(self, price_0: float, price_1: float):
        """
        Charge exchange fees.

        Args:
            price_0: Price before exchange.
            price_1: Price after exchange.
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
        assert price > 1e-16, f'Incorrect Price = {price}'

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
        assert price > 1e-16, f'Incorrect Price = {price}'

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
        assert price > 1e-16, f'Incorrect Price = {price}'

        x, y = self.to_xy(price)
        value_x = x + y / price
        return value_x

    def to_y(self, price: float) -> float:
        """
        Get value of UniswapV3 position expessed in Y.

        Args:
            price: Current price of X in Y currency.
        Returns:
            Total value of UniswapV3 position expessed in Y.
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
        | for linking in the backtest metrics, you can to add metrics here

        Args:
            timestamp: Timestamp of snapshot
            price: Current price of X in Y currency

        Returns: Position snapshot
        """
        x, y = self.to_xy(price)
        il_x, il_y = self.impermanent_loss(price)

        snapshot = {
                f'{self.name}_value_x': float(x + self.fees_x),
                f'{self.name}_value_y': float(y + self.fees_y),

                f'{self.name}_fees_x': float(self.fees_x),
                f'{self.name}_fees_y': float(self.fees_y),

                f'{self.name}_il_x': float(il_x),
                f'{self.name}_il_y': float(il_y),

                # f'{self.name}_total_rebalance_costs': self.total_rebalance_costs,
                # f'{self.name}_current_liquidity': self.liquidity
            }
        return snapshot
