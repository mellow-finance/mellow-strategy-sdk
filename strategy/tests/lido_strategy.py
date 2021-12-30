import sys
import os
root = os.getcwd()
sys.path.append(root)

import pandas as pd
import numpy as np
import pprint

from strategy.Data import PoolDataUniV3
from strategy.Strategies import LidoStrategy
from strategy.primitives import Pool, Token, Fee
from strategy.Backtest import Backtest


class LinearData:
    def __init__(self, pool, start_date='1-1-2022', freq='4H', n_points=2190, init_price=1, growth_rate=0.05):
        self.pool = pool
        self.start_date = start_date
        self.freq = freq
        self.n_points = n_points
        self.init_price = init_price
        self.growth_rate = growth_rate

    def generate_data(self):
        timestamps = pd.date_range(start=self.start_date, periods=self.n_points, freq=self.freq, normalize=True)
        prices = np.linspace(self.init_price, self.init_price * (1 + self.growth_rate), self.n_points)

        df = pd.DataFrame(data=zip(timestamps, prices), columns=['timestamp', 'price']).set_index('timestamp')

        df["price_before"] = df["price"].shift(1)
        df["price_before"] = df["price_before"].bfill()

        df["price_next"] = df["price"].shift(-1)
        df["price_next"] = df["price_next"].ffill()

        return PoolDataUniV3(self.pool, mints=None, burns=None, swaps=df)


def calc_perf(portfolio_history):
    df_stats = portfolio_history.portfolio_stats()

    snaphot_first = df_stats.iloc[0]
    snaphot_last = df_stats.iloc[-1]

    # portfolio returns
    return_x = snaphot_last['portfolio_value_to_x'] / snaphot_first['portfolio_value_to_x']
    return_y = snaphot_last['portfolio_value_to_y'] / snaphot_first['portfolio_value_to_y']
    # portfolio apy
    days = (snaphot_last.name - snaphot_first.name).days
    return_x_apy = return_x ** (365 / days) - 1
    return_y_apy = return_y ** (365 / days) - 1
    # price retruns apy
    price_return = snaphot_last['price'] / snaphot_first['price']
    price_return_apy = price_return ** (365 / days) - 1

    #IL - fees
    actual_loss_x = snaphot_last['total_il_to_x'] - snaphot_last['total_earned_fees_to_x']
    actual_loss_y = snaphot_last['total_il_to_y'] - snaphot_last['total_earned_fees_to_x']

    res = {
           'return_x': return_x,
           'return_y': return_y,
           'days': days,
           'return_x_apy': return_x_apy,
           'return_y_apy': return_y_apy,
           'price_return': price_return,
           'price_return_apy': price_return_apy,
           'actual_loss_x': actual_loss_x,
           'actual_loss_y': actual_loss_y,
           'last_portfolio_value_to_y': snaphot_last['portfolio_value_to_y']
    }

    return res


def init_strat(pool, interval_width):
    burn_gap = int(pool.fee.spacing * interval_width / 2) - 1
    lido = LidoStrategy(grid_width=pool.fee.spacing, interval_width_num=interval_width, burn_gap=burn_gap, pool=pool)
    return lido


def evaluate(interval_width):
    pool = Pool(Token.WETH, Token.stETH, Fee.LOW)
    data = LinearData(pool).generate_data()
    strat = init_strat(pool, interval_width)
    portfolio_history, rebalance_history, uni_history = Backtest(strat).backtest(data.swaps)
    metrics = calc_perf(portfolio_history)
    # metrics.update({'uni_coverage': uni_history.get_coverage(data.swaps)})
    return metrics


if __name__ == '__main__':
    out = evaluate(1)
    print(out)

