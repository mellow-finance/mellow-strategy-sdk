"""
    Test UniV3Position
    functions:
        mint - YES
        burn - YES
        charge_fees - YES
        swap_to_optimal - YES

    python -m unittest test/test_UniV3Position.py

"""


import unittest
from parameterized import parameterized
import numpy as np

from strategy.positions import UniV3Position


class TestUniswapLiquidityAligner(unittest.TestCase):
    """
        test UniswapLiquidityAligner
    """
    def setUp(self):
        self.pos = UniV3Position(
            name='TestPos',
            lower_price=10,
            upper_price=30,
            fee_percent=0.,
            gas_cost=1,
        )

    test_mint_bounds_arr = [
        ({'x': 0, 'y': 0, 'price': 9}, False),
        ({'x': 0, 'y': 5, 'price': 9}, True),
        ({'x': 1, 'y': 0, 'price': 9}, False),
        ({'x': 1, 'y': 5, 'price': 9}, True),
        ({'x': 0, 'y': 0, 'price': 10}, False),
        ({'x': 0, 'y': 5, 'price': 10}, True),
        ({'x': 1, 'y': 0, 'price': 10}, False),
        ({'x': 1, 'y': 5, 'price': 10}, True),
        ({'x': 0, 'y': 0, 'price': 30}, False),
        ({'x': 0, 'y': 5, 'price': 30}, False),
        ({'x': 1, 'y': 0, 'price': 30}, True),
        ({'x': 1, 'y': 5, 'price': 30}, True),
        ({'x': 0, 'y': 0, 'price': 31}, False),
        ({'x': 0, 'y': 5, 'price': 31}, False),
        ({'x': 1, 'y': 0, 'price': 31}, True),
        ({'x': 1, 'y': 5, 'price': 31}, True)
    ]

    @parameterized.expand(test_mint_bounds_arr)
    def test_mint_assert(self, input_val, expected):
        if expected:
            with self.assertRaises(Exception) as context:
                self.pos.mint(**input_val)
                self.assertTrue('Incorrect x' in str(context.exception))
        else:
            self.pos.mint(**input_val)

    test_mint_arr = [
        ({'x': 0, 'y': 0, 'price': 9}, 0.0),
        ({'x': 0.5555555555555556, 'y': 0, 'price': 9}, 4.156682932099112),
        ({'x': 1.6666666666666667, 'y': 0, 'price': 9}, 12.470048796297334),
        ({'x': 1, 'y': 0, 'price': 9}, 7.482029277778401),
        ({'x': 1.5555555555555556, 'y': 0, 'price': 9}, 11.638712209877513),
        ({'x': 2.666666666666667, 'y': 0, 'price': 9}, 19.95207807407574),
        ({'x': 10, 'y': 0, 'price': 9}, 74.820292777784),
        ({'x': 10.555555555555555, 'y': 0, 'price': 9}, 78.97697570988312),
        ({'x': 11.666666666666666, 'y': 0, 'price': 9}, 87.29034157408134),
        ({'x': 0, 'y': 0, 'price': 10}, 0.0),
        ({'x': 0.5, 'y': 0, 'price': 10}, 3.7410146388892005),
        ({'x': 1.5, 'y': 0, 'price': 10}, 11.223043916667601),
        ({'x': 1, 'y': 0, 'price': 10}, 7.482029277778401),
        ({'x': 1.5, 'y': 0, 'price': 10}, 11.223043916667601),
        ({'x': 2.5, 'y': 0, 'price': 10}, 18.705073194446),
        ({'x': 10, 'y': 0, 'price': 10}, 74.820292777784),
        ({'x': 10.5, 'y': 0, 'price': 10}, 78.5613074166732),
        ({'x': 11.5, 'y': 0, 'price': 10}, 86.04333669445161),
        ({'x': 0, 'y': 0, 'price': 30}, 0.0),
        ({'x': 0, 'y': 5, 'price': 30}, 2.15987580880501),
        ({'x': 0, 'y': 10, 'price': 30}, 4.31975161761002),
        ({'x': 0, 'y': 30, 'price': 30}, 12.959254852830062),
        ({'x': 0, 'y': 5, 'price': 30}, 2.15987580880501),
        ({'x': 0, 'y': 10, 'price': 30}, 4.31975161761002),
        ({'x': 0, 'y': 300, 'price': 30}, 129.59254852830063),
        ({'x': 0, 'y': 5, 'price': 30}, 2.15987580880501),
        ({'x': 0, 'y': 10, 'price': 30}, 4.31975161761002),
        ({'x': 0, 'y': 0, 'price': 31}, 0.0),
        ({'x': 0, 'y': 5, 'price': 31}, 2.15987580880501),
        ({'x': 0, 'y': 10, 'price': 31}, 4.31975161761002),
        ({'x': 0, 'y': 31, 'price': 31}, 13.391230014591063),
        ({'x': 0, 'y': 5, 'price': 31}, 2.15987580880501),
        ({'x': 0, 'y': 10, 'price': 31}, 4.31975161761002),
        ({'x': 0, 'y': 310, 'price': 31}, 133.91230014591065),
        ({'x': 0, 'y': 5, 'price': 31}, 2.15987580880501),
        ({'x': 0, 'y': 10, 'price': 31}, 4.31975161761002)
    ]

    @parameterized.expand(test_mint_arr)
    def test_mint(self, input_val, expected):
        self.pos.mint(**input_val)

        self.assertAlmostEqual(self.pos.liquidity, expected, 8)
        self.assertAlmostEqual(self.pos.x_hold, input_val['x'])
        self.assertAlmostEqual(self.pos.y_hold, input_val['y'])

        self.assertAlmostEqual(self.pos.total_gas_costs, self.pos.gas_cost)

    @parameterized.expand(test_mint_arr)
    def test_double_mint(self, input_val, expected):
        self.pos.mint(**input_val)
        self.pos.mint(**input_val)

        self.assertAlmostEqual(self.pos.liquidity, 2*expected, 8)
        self.assertAlmostEqual(self.pos.x_hold, 2*input_val['x'])
        self.assertAlmostEqual(self.pos.y_hold, 2*input_val['y'])

        self.assertAlmostEqual(self.pos.total_gas_costs, 2*self.pos.gas_cost)

    def test_burn_assert(self):
        self.pos.mint(x=100, y=0, price=10)

        with self.assertRaises(Exception) as context:
            self.pos.burn(liq=1e6, price=10)
            self.assertTrue('Too much liquidity too withdraw' in str(context.exception))

        with self.assertRaises(Exception) as context:
            self.pos.burn(liq=0, price=10)
            self.assertTrue('Too small liquidity too withdraw' in str(context.exception))

    test_burn_lite_arr = [
        ({'liq': 74.820292777784, 'price': 9}, (10.0, 0.0)),
        ({'liq': 74.820292777784, 'price': 10}, (10.0, 0.0)),
        ({'liq': 74.820292777784, 'price': 15}, (5.658262487936979, 53.17520750827662)),
        ({'liq': 74.820292777784, 'price': 30}, (0.0, 173.20508075688775)),
        ({'liq': 74.820292777784, 'price': 31}, (0.0, 173.20508075688775)),
        ({'liq': 149.640585555568, 'price': 9}, (20.0, 0.0)),
        ({'liq': 149.640585555568, 'price': 10}, (20.0, 0.0)),
        ({'liq': 149.640585555568, 'price': 15}, (11.316524975873959, 106.35041501655324)),
        ({'liq': 149.640585555568, 'price': 30}, (0.0, 346.4101615137755)),
        ({'liq': 149.640585555568, 'price': 31}, (0.0, 346.4101615137755)),
        ({'liq': 748.20292777784, 'price': 9}, (100.0, 0.0)),
        ({'liq': 748.20292777784, 'price': 10}, (100.0, 0.0)),
        ({'liq': 748.20292777784, 'price': 15}, (56.582624879369796, 531.7520750827663)),
        ({'liq': 748.20292777784, 'price': 30}, (0.0, 1732.0508075688774)),
        ({'liq': 748.20292777784, 'price': 31}, (0.0, 1732.0508075688774))
    ]

    @parameterized.expand(test_burn_lite_arr)
    def test_burn_lite(self, input_val, expected):
        self.pos.mint(x=100, y=0, price=10)
        liq_total = self.pos.liquidity
        ans = self.pos.burn(**input_val)

        self.assertTrue(np.allclose(ans, expected, atol=1e-08, rtol=0))

        self.assertAlmostEqual(liq_total - self.pos.liquidity, input_val['liq'], 8)

        self.assertAlmostEqual(self.pos.total_gas_costs, self.pos.gas_cost + self.pos.gas_cost, 8)


    def test_burn_loss(self):
        self.pos.mint(x=100, y=0, price=10)
        liq_total = self.pos.liquidity
        self.pos.burn(liq_total, price=20)

        self.assertTrue(np.allclose(
            (self.pos.realized_loss_to_x, self.pos.realized_loss_to_y),
            (20.29728907254264, 405.9457814508528),
            atol=1e-08, rtol=0)
        )

        self.assertAlmostEqual(self.pos.total_gas_costs, self.pos.gas_cost + self.pos.gas_cost, 8)

    test_charge_fees_arr = [
        ({'price_0': 9, 'price_1': 9}, (0.0, 0)),
        ({'price_0': 9, 'price_1': 10}, (0.0, 0)),
        ({'price_0': 9, 'price_1': 11}, (0, 57.741487350018005)),
        ({'price_0': 9, 'price_1': 30}, (0, 866.0254037844387)),
        ({'price_0': 9, 'price_1': 31}, (0, 866.0254037844387)),
        ({'price_0': 10, 'price_1': 9}, (0.0, 0)),
        ({'price_0': 10, 'price_1': 10}, (0.0, 0)),
        ({'price_0': 10, 'price_1': 11}, (0, 57.741487350018005)),
        ({'price_0': 10, 'price_1': 30}, (0, 866.0254037844387)),
        ({'price_0': 10, 'price_1': 31}, (0, 866.0254037844387)),
        ({'price_0': 11, 'price_1': 9}, (5.505434803563979, 0)),
        ({'price_0': 11, 'price_1': 10}, (5.505434803563979, 0)),
        ({'price_0': 11, 'price_1': 11}, (0.0, 0)),
        ({'price_0': 11, 'price_1': 30}, (0, 808.2839164344207)),
        ({'price_0': 11, 'price_1': 31}, (0, 808.2839164344207)),
        ({'price_0': 30, 'price_1': 9}, (50.0, 0)),
        ({'price_0': 30, 'price_1': 10}, (50.0, 0)),
        ({'price_0': 30, 'price_1': 11}, (44.49456519643602, 0)),
        ({'price_0': 30, 'price_1': 30}, (0.0, 0)),
        ({'price_0': 30, 'price_1': 31}, (0.0, 0)),
        ({'price_0': 31, 'price_1': 9}, (50.0, 0)),
        ({'price_0': 31, 'price_1': 10}, (50.0, 0)),
        ({'price_0': 31, 'price_1': 11}, (44.49456519643602, 0)),
        ({'price_0': 31, 'price_1': 30}, (0.0, 0)),
        ({'price_0': 31, 'price_1': 31}, (0.0, 0))
    ]

    @parameterized.expand(test_charge_fees_arr)
    def test_charge_fees(self, input_val, expected):
        self.pos = UniV3Position(
            name='TestPos',
            lower_price=10,
            upper_price=30,
            fee_percent=0.5,
            gas_cost=1,
        )

        self.pos.mint(x=100, y=0, price=10)
        self.pos.charge_fees(**input_val)

        self.assertAlmostEqual(self.pos._fees_x_earned_, expected[0])
        self.assertAlmostEqual(self.pos._fees_y_earned_, expected[1])


if __name__ == "__main__":
    unittest.main()
