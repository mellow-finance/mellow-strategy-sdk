"""
    Test UniV3Position
    functions:
        mint TODO
        burn
        charge_fees
        impermanent_loss -
        impermanent_loss_to_x -
        impermanent_loss_to_y -
        swap_to_optimal -

    cd tests_pytest && python -m unittest UniV3Position_test.py
"""

import sys
sys.path.append('..')

import unittest
from parameterized import parameterized


from strategy.uniswap_utils import UniswapLiquidityAligner



class TestUniswapLiquidityAligner(unittest.TestCase):
    """
        test UniswapLiquidityAligner
    """
    def setUp(self):
        self.aligner = UniswapLiquidityAligner(10, 30)

    @parameterized.expand(test_xy_to_optimal_liq_arr)
    def test_xy_to_optimal_liq(self, input_val, expected):
        """
            run test
        Returns:
        """
        # работает, оставляю на всякий
        # sys.stdout.write('\n\n\nssssss\n\n\n')

        ans = self.aligner.xy_to_liq(**input_val)

        self.assertAlmostEqual(ans, expected, 8)

    def test_xy_to_optimal_liq_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.xy_to_liq(x=1, y=1, price=-1)
        self.assertTrue('Incorrect price' in str(context.exception))

    def test_xy_to_optimal_liq_assert_x(self):
        with self.assertRaises(Exception) as context:
            self.aligner.xy_to_liq(x=-1, y=1, price=1)
        self.assertTrue('Incorrect x' in str(context.exception))

    def test_xy_to_optimal_liq_assert_y(self):
        with self.assertRaises(Exception) as context:
            self.aligner.xy_to_liq(x=1, y=-1, price=1)
        self.assertTrue('Incorrect y' in str(context.exception))

    @parameterized.expand(test_liq_to_optimal_xy_arr)
    def test_liq_to_optimal_xy(self, input_val, expected):
        """
            run test
        Returns:
        """

        ans = UniswapLiquidityAligner(10, 30).liq_to_optimal_xy(**input_val)

        self.assertAlmostEqual(ans, expected, 8)

    def test_liq_to_optimal_xy_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.liq_to_optimal_xy(price=0, liq=1)
        self.assertTrue('Incorrect price' in str(context.exception))

    def test_liq_to_optimal_xy_assert_liquidity(self):
        with self.assertRaises(Exception) as context:
            self.aligner.liq_to_optimal_xy(price=1, liq=-1)
        self.assertTrue('Incorrect liquidity' in str(context.exception))

    @parameterized.expand(test_check_xy_is_optimal_arr)
    def test_check_xy_is_optimal(self, input_val, expected):
        """
            run test
        Returns:
        """

        ans = UniswapLiquidityAligner(10, 30).check_xy_is_optimal(**input_val)

        self.assertAlmostEqual(ans, expected, 8)

    def test_check_xy_is_optimal_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.check_xy_is_optimal(price=-1, x=1, y=1)
        self.assertTrue('Incorrect price' in str(context.exception))

    def test_check_xy_is_optimal_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.check_xy_is_optimal(price=1, x=-1, y=1)
        self.assertTrue('Incorrect x' in str(context.exception))

    def test_check_xy_is_optimal_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.xy_to_liq(price=1, x=1, y=-1)
        self.assertTrue('Incorrect y' in str(context.exception))


if __name__ == "__main__":
    unittest.main()
