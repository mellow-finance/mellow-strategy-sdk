Getting Started
===============

The easiest way to get started is to use 

Example::

    from strategy.primitives import Frequency, Pool, Token
    from strategy.backtest import Backtest, AbstractStrategy

    class Strategy(AbstractStrategy):        
        def rebalance(
            self,
            t: datetime,
            c: float,
            vol: float,
            l: Callable[[float], float],
            pool_data: PoolData,
        ) -> bool:
            if not self.portfolio.position("main"):
                self.portfolio.add_position(Position(id="main", a = c / 2, b = c * 2))
                pos = self.portfolio.position("main")
                pos.deposit(c, 1)
            return False

    strategy = Strategy()
    backtest = Backtest(strategy)
    backtest.run_for_pool(Pool(Token.WBTC, Token.USDC, Fee.MIDDLE), Frequency.DAY, 0.001)
    backtest.plot()