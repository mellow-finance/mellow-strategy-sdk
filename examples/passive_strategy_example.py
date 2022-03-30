import sys
import polars as pl

from strategy.data import SyntheticData
from strategy.backtest import Backtest
from strategy.strategies import UniV3Passive
from strategy.primitives import Pool, Token, Fee


def evaluate() -> pl.DataFrame:
    """
    Evaluate backtesting.
    Args:
        path: Path to data.
    Returns:
        Performance metrics.
    """
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    data = SyntheticData(pool, init_price=10, mu=0.005).generate_data()

    # data = RawDataUniV3(pool).load_from_folder()
    m_strat = UniV3Passive(
        lower_price=data.swaps['price'].min(),
        upper_price=data.swaps['price'].max(),
        pool=pool,
        gas_cost=0.,
        name='passive'
    )

    portfolio_history, _, _ = Backtest(m_strat).backtest(data.swaps)
    metrics = portfolio_history.calculate_stats()
    return metrics.tail()


if __name__ == '__main__':
    out = evaluate()
    print(out)
