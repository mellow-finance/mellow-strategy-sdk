Getting Started
===============

TODO: install libs

The easiest way to get started is to clone SDK and use examples in the `Github repo <https://github.com/mellow-finance/mellow-strategy-sdk/tree/main/examples>`_.
It will also be useful to look at the tests  `Github repo <https://github.com/mellow-finance/mellow-strategy-sdk/tree/main/tests>`_.

A typical notebook would start with downloading and preparing data for a specific pool::

    from strategy.data import RawDataUniV3
    from strategy.primitives import Pool, Token, Fee
    pool = Pool(Token.WBTC, Token.WETH, Fee.MIDDLE)
    data = RawDataUniV3(pool).load_from_folder()

Next optional step is for visualizing the data in the notebook::

    LiquidityViewer(data).draw_plot() # Optional step to visualize the data in the notebook

Then you define your strategy by inheriting :ref:`class AbstractStrategy` and overriding the ``rebalance`` method::

    from strategy.strategies import AbstractStrategy
    from strategy.uniswap_utils import UniswapLiquidityAligner
    from strategy.positions import UniV3Position

    class UniV3Passive(AbstractStrategy):
        """
        ``UniV3Passive`` is the passive strategy on UniswapV3 without rebalances.

        Attributes:
            lower_price: Lower bound of the interval
            upper_price: Upper bound of the interval
            rebalance_cost: Rebalancing cost, expressed in currency
            pool: UniswapV3 Pool instance
            name: Unique name for the instance
        """
        def __init__(self,
                     lower_price: float,
                     upper_price: float,
                     pool: Pool,
                     rebalance_cost: float,
                     name: str = None,
                     ):
            super().__init__(name)
            self.lower_price = lower_price
            self.upper_price = upper_price
            self.decimal_diff = -pool.decimals_diff
            self.fee_percent = pool.fee.percent
            self.rebalance_cost = rebalance_cost

        def rebalance(self, *args, **kwargs) -> bool:
            timestamp = kwargs['timestamp']
            row = kwargs['row']
            portfolio = kwargs['portfolio']
            price_before, price = row['price_before'], row['price']

            is_rebalanced = None

            if len(portfolio.positions) == 0:
                univ3_pos = self.create_uni_position(price)
                portfolio.append(univ3_pos)
                is_rebalanced = 'mint'

            if 'UniV3Passive' in portfolio.positions:
                uni_pos = portfolio.get_position('UniV3Passive')
                uni_pos.charge_fees(price_before, price)

            return is_rebalanced


        def create_uni_position(self, price):
            uni_aligner = UniswapLiquidityAligner(self.lower_price, self.upper_price)
            x_uni_aligned, y_uni_aligned = uni_aligner.align_to_liq(1 / price, 1, price)
            univ3_pos = UniV3Position('UniV3Passive', self.lower_price, self.upper_price, self.fee_percent, self.rebalance_cost)
            univ3_pos.deposit(x_uni_aligned, y_uni_aligned, price)
            return univ3_pos

Typycally the definition of the ``rebalance`` method would contain two sections:

- `Init`
            On the first call you need to initialize strategy's portfolio under management.
            Here you need to create initial positions with ``append``
            method of :ref:`class Portfolio` and invest initial amount using ``deposit`` method.
- `Rebalance`
            In this section you decide if you want to rebalance or not.
            If you rebalance you need to implement the logic of rebalance.

The final step is to run backtest using your strategy and data::

    from strategy.backtest import Backtest

    univ3_passive = UniV3Passive(1e-6, 1e6, pool, 0.01)
    b = Backtest(univ3_passive)
    portfolio_history, rebalance_history, uni_history = b.backtest(data.swaps)

Next visualize results::

    # Draw rebalances
    rv = RebalanceViewer(rebalance_history)
    rv.draw_rebalances(data.swaps)
    # Draw Uniswap intervals
    uv = UniswapViewer(uni_history)
    uv.draw_intervals(data.swaps)
    # Calculate Uniswap intervals coverage
    uni_history.get_coverage(data.swaps)
    # Draw portfolio stats, like value, fees earned, apy
    fig1, fig2, fig3, fig4 = PotrfolioViewer(portfolio_history, pool).draw_portfolio()

Congratulations! Now you have the results of your strategy backtest on the real UniV3 data!