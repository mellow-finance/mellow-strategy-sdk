"""
TODO write
"""
import warnings
import sys
sys.path.append('..')

from strategy.data import RawDataUniV3
from strategy.backtest import Backtest
from strategy.strategies import HStrategy
from strategy.primitives import Pool, Token, Fee


warnings.filterwarnings('ignore')


def init_strat(data, pool):
    """
    Initilize strategy.
    Args:
        data: UniswapV3 data.
        pool: UniswapV3 pool.
    Returns:
        Initialized strategy.
    """
    lower_0 = data.swaps['price'].min() - 2
    upper_0 = data.swaps['price'].max() + 2
    h_strat = HStrategy(900, 10, 1200, lower_0, upper_0, 60, 15, pool, 0.01, 1e-5, 1e-5)
    return h_strat


def evaluate():
    """
    Evaluate backtesting.
    Args:
        path: Path to data.
    Returns:
        Performance metrics.
    """
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    data = RawDataUniV3(pool).load_from_folder()
    strat = init_strat(data, pool)
    portfolio_history, _, uni_history = Backtest(strat).backtest(data.swaps)
    metrics = portfolio_history.calculate_stats()
    print('Uni Coverage = ', uni_history.get_coverage(data.swaps))
    return metrics.tail()


if __name__ == '__main__':
    out = evaluate()
    print(out)
