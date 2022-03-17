from typing import List, Hashable
from strategy.strategies import AbstractStrategy


class MultiStrategy(AbstractStrategy):
    """
    ``MultiStrategy`` is used for making composition of several strategies.

    Attributes:
        name: Unique name for the instance.
        strategies: List of strategies.
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

    def remove(self, name: str) -> None:
        """
        Remove strategy from composition by name.

        Args:
            name: Strategy name.
        """
        if name not in self.strategies:
            raise Exception(f'Invalid name = {name}')
        del self.strategies[name]

    def rebalance(self, *args: list, **kwargs: dict) -> Hashable:
        """
        Rebalance implementation for strategy composition.

        Args:
            args: Any args.
            kwargs: Any kwargs.

        Returns: Rebalnaces status of each strategy in composition.
        """
        status = [strategy.rebalance(*args, **kwargs) for name, strategy in self.strategies.items()]
        status_cleaned = [st for st in status if st is not None]
        if len(status_cleaned) == 0:
            is_rebalanced = None
        elif len(status_cleaned) == 1:
            is_rebalanced = status_cleaned[0]
        else:
            is_rebalanced = 'multi_call'
        return is_rebalanced
