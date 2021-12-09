import pprint
import sys
import os
root = os.getcwd()
sys.path.append(root)

from strategy.Data import SyntheticData, RawDataUniV3
from strategy.Backtest import Backtest
from strategy.Strategies import MBStrategy
from strategy.primitives import Pool, Token, Fee


def init_strat(data, pool):
    lower_0 = data.swaps['price'].min()
    upper_0 = data.swaps['price'].max()
    bi_strat = MBStrategy(600, 30, lower_0, upper_0, pool, 0.03,  0.0002, 0.0002)
    return bi_strat

def calc_perf(portfolio_history, data):
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
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    # data = SyntheticData(pool, init_price=10, mu=0.005).generate_data()
    data = RawDataUniV3(pool, folder=f'{path}/data/').load_from_folder()
    bi_strat = init_strat(data, pool)
    portfolio_history, rebalance_history, uni_history = Backtest(bi_strat).backtest(data.swaps)
    metrics = calc_perf(portfolio_history, data)
    return metrics
    

if __name__ == '__main__':
    out = evaluate(root)
    pprint.pprint(out)