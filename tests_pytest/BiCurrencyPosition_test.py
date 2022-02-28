"""
    Test BiCurrencyPosition
    functions:
        rebalance, interest_gain, swap_x_to_y, swap_y_to_x,
        rebalance - YES
        interest_gain - TODO

        cd tests_pytest and python -m unittest BiCurrencyPosition_test.py
"""


import sys
sys.path.append('..')

import numpy as np
import unittest


from strategy.positions import BiCurrencyPosition


class TestBiCurrencyPosition(unittest.TestCase):
    """
        test BiCurrencyPosition
    """

    def test_rebalance_1(self):
        """
            run test
        Returns:
        """
        pos = BiCurrencyPosition(
            name='',
            swap_fee=0.0003,
            rebalance_cost=0.01,
            x=0,
            y=1,
        )

        pos.rebalance(x_fraction=0.3, y_fraction=0.7, price=0.3)

        self.assertTrue(np.allclose([pos.x, pos.y, pos.total_rebalance_costs], [0.9997, 0.7, 0.01], atol=1e-08, rtol=0))

    def test_rebalance_2(self):
        """
            run test
        Returns:
        """
        pos = BiCurrencyPosition(
            name='',
            swap_fee=0.0003,
            rebalance_cost=0.01,
            x=0.5,
            y=4
        )
        pos.rebalance(x_fraction=0.7, y_fraction=0.3, price=100)

        self.assertTrue(
            np.allclose([pos.x, pos.y, pos.total_rebalance_costs], [0.378, 16.19634, 0.01], atol=1e-08, rtol=0)
        )

    def test_rebalance_3(self):
        """
            run test
        Returns:
        """
        pos = BiCurrencyPosition(
            name='',
            swap_fee=0.0000,
            rebalance_cost=1000,
            x=1,
            y=4
        )
        pos.rebalance(x_fraction=0.2, y_fraction=0.8, price=1)

        self.assertTrue(
            np.allclose([pos.x, pos.y, pos.total_rebalance_costs], [0.2, 0.8, 0.0], atol=1e-08, rtol=0)
        )


if __name__ == "__main__":
    unittest.main()
