import pprint
import sys
import os
root = os.getcwd()
sys.path.append(root)

from strategy.Data import SyntheticData, RawDataUniV3
from strategy.Backtest import Backtest
from strategy.Strategies import MUStrategy, MBStrategy
from strategy.MultiStrategy import MultiStrategy
from strategy.primitives import Pool, Token, Fee


def init_strat(pool, data):
    """
    Initilize strategy.
    Args:
        pool: UniswapV3 pool.
        data: UniswapV3 data.
    Returns:
        Initialized strategy.
    """
    lower_0 = data.swaps['price'].min()
    upper_0 = data.swaps['price'].max()
    mb_strat = MBStrategy(600, 30, lower_0, upper_0, pool, 0.01,  0.0002, 0.0002)
    mu_strat = MUStrategy(10, 360, 60, 3, 30, lower_0, upper_0, pool, 0.01)
    ms = MultiStrategy('Multi', [mb_strat, mu_strat])
    return ms


def calc_perf(portfolio_history, data):
    """
    Calculate strategy performance metrics.
    Args:
        data: UniswapV3 data.
        pool: UniswapV3 pool.
    Returns:
        Performance metrics.
    """
    snaphot_last = portfolio_history.snapshots[-1]
    snaphot_first = portfolio_history.snapshots[0]
    
    return_x = snaphot_last['Vault_value_to_x'] / snaphot_first['Vault_value_to_x']
    return_y = snaphot_last['Vault_value_to_y'] / snaphot_first['Vault_value_to_y']
    
    days = (snaphot_last['timestamp'] - snaphot_first['timestamp']).days
    return_x_apy = return_x**(365 / days) - 1
    return_y_apy = return_y**(365 / days) - 1
    
    price_0 = data.swaps['price'].values[0]
    price_1 = data.swaps['price'].values[-1]
    price_return = price_1 / price_0
    price_return_apy = price_return**(365 / days) - 1
    
    res = {'return_x': return_x, 
           'return_y': return_y, 
           'days': days, 
           'return_x_apy': return_x_apy,
           'return_y_apy': return_y_apy,
           'price_return': price_return,
           'price_return_apy': price_return_apy}
    
    return res


def evaluate(path):
    """
    Evaluate backtesting.
    Args:
        path: Path to data.
    Returns:
        Performance metrics.
    """
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    data = RawDataUniV3(pool, folder=f'{path}/data/').load_from_folder()
    strat = init_strat(pool, data)
    portfolio_history, rebalance_history, uni_history = Backtest(strat).backtest(data.swaps)
    metrics = calc_perf(portfolio_history, data)
    print('Uni Coverage = ', uni_history.get_coverage(data.swaps))
    return metrics


if __name__ == '__main__':
    out = evaluate(root)
    pprint.pprint(out)
