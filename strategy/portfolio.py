from typing import List, Tuple
from datetime import datetime
import numpy as np

from strategy.positions import BiCurrencyPosition, AbstractPosition, UniV3Position
from strategy.uniswap_utils import UniswapLiquidityAligner


class Portfolio(AbstractPosition):
    """
    ``Portfolio`` is a container for several open positions.

    Attributes:
        name: Unique name for the position.
        positions: List of initial positions.
    """

    def __init__(
            self, name: str, rebalance_cost, swap_fee, fee_percent, x_interest=None,
            y_interest=None,positions: List[AbstractPosition] = None
    ):
        super().__init__(name)

        if positions is None:
            positions = []
        self.positions = {pos.name: pos for pos in positions}

        self.swap_fee = swap_fee
        self.fee_percent = fee_percent
        self.x_interest = x_interest
        self.y_interest = y_interest
        self.rebalance_cost = rebalance_cost

        self.positions['main_vault'] = BiCurrencyPosition(
            name='main_vault',
            swap_fee=self.swap_fee,
            rebalance_cost=self.rebalance_cost,
            main_vault=None,
            x=0,
            y=0,
            x_interest=self.x_interest,
            y_interest=self.y_interest
        )

    def deposit(self, x, y):
        self.positions['main_vault'].deposit(x, y)

    def withdraw(self, x, y):
        self.positions['main_vault'].withdraw(x, y)

    def add_univ3_pos(self, name, lower_price, upper_price):
        new_pos = UniV3Position(
            name=name,
            lower_price=lower_price,
            upper_price=upper_price,
            fee_percent=self.fee_percent,
            rebalance_cost=self.rebalance_cost,
            main_vault=self.positions['main_vault']
        )
        self.append(new_pos)

        return new_pos

    def add_bicur_pos(self, name):
        new_pos = BiCurrencyPosition(
            name=name,
            swap_fee=self.swap_fee,
            rebalance_cost=self.rebalance_cost,
            main_vault=self.positions['main_vault'],
            x=0,
            y=0,
            x_interest=self.x_interest,
            y_interest=self.y_interest
        )
        self.append(new_pos)

        return new_pos

    def swap_and_deposit(self, x, y, price, univ3_pos: UniV3Position):
        x_uni, y_uni = self.swap_to_optimal(
            x=x, y=y, price=price, lower_price=univ3_pos.lower_price, upper_price=univ3_pos.upper_price
        )
        univ3_pos.deposit(x=x_uni, y=y_uni, price=price)

    def swap_to_optimal(
            self, x: float, y: float, price: float, lower_price: float, upper_price: float
    ) -> Tuple[float, float]:
        """
        For price and amounts perform swap to token amounts that can be completely mint.

        Args:
            x: number of tokens X
            y: number of tokens X
            price: current market price
            lower_price: lower bound of the interval (price)
            upper_price: upper bound of the interval (price)
        Returns:
            (optimal number of tokens X, optimal number of tokens Y)
        """

        sqrt_price = np.sqrt(price)
        sqrt_lower = np.sqrt(lower_price)
        sqrt_upper = np.sqrt(upper_price)

        aligner = UniswapLiquidityAligner(lower_price, upper_price)

        if aligner.check_xy_is_optimal(x=x, y=y, price=price)[0]:
            return x, y

        if price <= lower_price:
            dx = self.positions['main_vault'].swap_y_to_x(dy=y, price=price)
            return x + dx, 0

        if price >= upper_price:
            dy = self.positions['main_vault'].swap_x_to_y(dx=x, price=price)
            return 0, y + dy

        price_real = (sqrt_price - sqrt_lower) * sqrt_upper * sqrt_price / (sqrt_upper - sqrt_price)

        v_y = price * x + y
        x_new = v_y / (price + price_real)
        y_new = price_real * x_new

        # TODO It is necessary to add accounting for the commission,
        #  since after the commission the tokens become smaller and are not deposited in the interval

        if x_new < x:
            dy = self.positions['main_vault'].swap_x_to_y(dx=x - x_new, price=price)
            # Seems like. work but I am not sure
            return x_new, y + dy
        else:
            dx = self.positions['main_vault'].swap_y_to_x(dy=y - y_new, price=price)
            # Seems like. work but I am not sure
            return x + dx, y_new

        # return x_new, y_new

    def rename_position(self, current_name: str, new_name: str) -> None:
        """
        Rename position in portfolio by its name.

        Args:
            current_name: Current name of position.
            new_name: New name for position.
        """
        self.positions[current_name].rename(new_name)
        self.positions[new_name] = self.positions.pop(current_name)

    def append(self, position: AbstractPosition) -> None:
        """
        Add position to portfolio.

        Args:
            position: Any ``AbstractPosition`` instance.
        """
        self.positions[position.name] = position

    def remove(self, name: str) -> None:
        """
        Remove position from portfolio by its name.

        Args:
            name: Position name.
        """
        if name not in self.positions:
            raise Exception(f'Invalid name = {name}')
        del self.positions[name]

    def get_position(self, name: str) -> AbstractPosition:
        """
        Get position from portfolio by name.

        Args:
            name: Position name.

        Returns:
            ``AbstractPosition`` instance.
        """
        return self.positions.get(name, None)

    def get_last_position(self) -> AbstractPosition:
        """
        Get last position from portfolio.

        Returns:
             Last position in portfolio.
        """
        if self.positions:
            last_key = list(self.positions.keys())[-1]
            pos = self.get_position(last_key)
            return pos
        else:
            raise Exception('Position not found')

    def positions_list(self) -> List[AbstractPosition]:
        """
        Get list of all positions in portfolio.

        Returns:
            List of all positions in portfolio.
        """
        return list(self.positions.values())

    def position_names(self) -> List[str]:
        """
        Get list of position names in portfolio.

        Returns:
            List of all position names in portfolio.
        """
        return list(self.positions.keys())

    def to_x(self, price: float) -> float:
        """
        Get total value of portfolio denominated to X.

        Args:
            price: Current price of X in Y currency

        Returns:
            Total value of portfolio denominated in X
        """
        total_x = 0
        for _, pos in self.positions.items():
            total_x += pos.to_x(price)
        return total_x

    def to_y(self, price: float) -> float:
        """
        Get total value of portfolio expressed in Y

        Args:
            price: Current price of X in Y currency

        Returns:
            Total value of portfolio denominated in Y
        """
        total_y = 0
        for _, pos in self.positions.items():
            total_y += pos.to_y(price)
        return total_y

    def to_xy(self, price: float) -> Tuple[float, float]:
        """
        Get amount of X and amount of Y in portfolio

        Args:
            price: Current price of X in Y currency.

        Returns:
            (amount of X, amount of Y)
        """
        total_x = 0
        total_y = 0
        for _, pos in self.positions.items():
            x, y = pos.to_xy(price)
            total_x += x
            total_y += y
        return total_x, total_y

    def snapshot(self, timestamp: datetime, price: float) -> dict:

        """
        | Get portfolio snapshot.
        | Used in PortfolioHistory.add_snapshot() to collect backtest data.

        Args:
            timestamp: Timestamp of snapshot
            price: Current price of X in Y currency

        Returns: Position snapshot
        """
        snapshot = {'timestamp': timestamp, 'price': price}
        for _, pos in self.positions.items():
            snapshot.update(pos.snapshot(timestamp, price))
        return snapshot
