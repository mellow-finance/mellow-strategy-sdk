from .Strategies import AbstractStrategy
from typing import List


class MultiStrategy(AbstractStrategy):
    def __init__(self, name: str = None, strategies: List[AbstractStrategy] = None):
        super().__init__(name)
        if strategies is None:
            strategies = []
        self.strategies = {strat.name: strat for strat in strategies}

    def append(self, strategy: AbstractStrategy) -> None:
        self.strategies[strategy.name] = strategy
        return None

    def remove(self, name: str) -> None:
        if name not in self.strategies:
            raise Exception(f'Invalid name = {name}')
        del self.strategies[name]
        return None

    def rebalance(self, *args, **kwargs) -> bool:
        is_rebalanced = [False, ]
        for name, strategy in self.strategies.items():
            status = strategy.rebalance(*args, **kwargs)
            is_rebalanced.append(status)
        return any(is_rebalanced)
