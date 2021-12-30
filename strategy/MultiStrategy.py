from .Strategies import AbstractStrategy
from typing import List


class MultiStrategy(AbstractStrategy):
    """
        ``MultiStrategy`` is used for making composition of several strategies.
        Attributes:
            name: Unique name for the instance
            strategies: List of strategies
    """
    def __init__(self, name: str = None, strategies: List[AbstractStrategy] = None):
        super().__init__(name)
        if strategies is None:
            strategies = []
        self.strategies = {strat.name: strat for strat in strategies}

    def append(self, strategy: AbstractStrategy) -> None:
        """
        Add strategy to composition.
        Args:
            strategy: Any AbstractStrategy.
        """
        self.strategies[strategy.name] = strategy
        return None

    def remove(self, name: str) -> None:
        """
        Remove strategy from composition by name.
        Args:
            name: Strategy name.
        """
        if name not in self.strategies:
            raise Exception(f'Invalid name = {name}')
        del self.strategies[name]
        return None

    def rebalance(self, *args: list, **kwargs: dict) -> list:
        """
        Rebalance implementation for strategy composition.
        Args:
            args: Any args.
            kwargs: Any kwargs.
        Returns: Rebalnaces status of each strategy in composition.
        """
        status = [strategy.rebalance(*args, **kwargs) for name, strategy in self.strategies.items()]
        return status
