"""
TODO write
"""

import sys

sys.path.append('..')

import polars as pl

from strategy.data import SyntheticData, RawDataUniV3
from strategy.backtest import Backtest
from strategy.strategies import MStrategy
from strategy.primitives import Pool, Token, Fee


def init_strat(data, pool):
    """
    Initilize strategy.
    Args:
        data: UniswapV3 data.
        pool: UniswapV3 pool.
    Returns:
        Initialized strategy.
    """
    lower_0 = data.swaps['price'].min()
    upper_0 = data.swaps['price'].max()
    bi_strat = MStrategy(600, lower_0, upper_0, pool, 0.01, 1e-6, 1e-6)
    return bi_strat


def evaluate() -> pl.DataFrame:
    """
    Evaluate backtesting.
    Args:
        path: Path to data.
    Returns:
        Performance metrics.
    """
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    # data = SyntheticData(pool, init_price=10, mu=0.005).generate_data()
    data = RawDataUniV3(pool).load_from_folder()
    m_strat = init_strat(data, pool)

    portfolio_history, _, _ = Backtest(m_strat).backtest(data.swaps)
    metrics = portfolio_history.calculate_stats()
    return metrics.tail()


if __name__ == '__main__':
    out = evaluate()
    print(out)
