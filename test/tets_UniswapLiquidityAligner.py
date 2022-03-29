"""
    Test  UniswapLiquidityAligner
    functions:
        xy_to_liq - Yes
        liq_to_optimal_xy - Yes
        check_xy_is_optimal - Yes

    python -m unittest test/tets_UniswapLiquidityAligner.py
"""

import numpy as np
import unittest
from parameterized import parameterized
import sys

from strategy.uniswap_utils import UniswapLiquidityAligner


# TODO - make it possible to call one test
test_xy_to_optimal_liq_arr = [
    ({'x': 0, 'y': 0, 'price': 9}, 0.0),
    ({'x': 0, 'y': 0, 'price': 10}, 0.0),
    ({'x': 0, 'y': 0, 'price': 15}, 0.0),
    ({'x': 0, 'y': 0, 'price': 30}, 0.0),
    ({'x': 0, 'y': 0, 'price': 31}, 0.0),
    ({'x': 0, 'y': 2, 'price': 9}, 0.0),
    ({'x': 0, 'y': 2, 'price': 10}, 0.0),
    ({'x': 0, 'y': 2, 'price': 15}, 0.0),
    ({'x': 0, 'y': 2, 'price': 30}, 0.8639503235220041),
    ({'x': 0, 'y': 2, 'price': 31}, 0.8639503235220041),
    ({'x': 0, 'y': 20, 'price': 9}, 0.0),
    ({'x': 0, 'y': 20, 'price': 10}, 0.0),
    ({'x': 0, 'y': 20, 'price': 15}, 0.0),
    ({'x': 0, 'y': 20, 'price': 30}, 8.63950323522004),
    ({'x': 0, 'y': 20, 'price': 31}, 8.63950323522004),
    ({'x': 1, 'y': 0, 'price': 9}, 7.482029277778401),
    ({'x': 1, 'y': 0, 'price': 10}, 7.482029277778401),
    ({'x': 1, 'y': 0, 'price': 15}, 0.0),
    ({'x': 1, 'y': 0, 'price': 30}, 0.0),
    ({'x': 1, 'y': 0, 'price': 31}, 0.0),
    ({'x': 1, 'y': 2, 'price': 9}, 7.482029277778401),
    ({'x': 1, 'y': 2, 'price': 10}, 7.482029277778401),
    ({'x': 1, 'y': 2, 'price': 15}, 2.814104402550319),
    ({'x': 1, 'y': 2, 'price': 30}, 0.8639503235220041),
    ({'x': 1, 'y': 2, 'price': 31}, 0.8639503235220041),
    ({'x': 1, 'y': 20, 'price': 9}, 7.482029277778401),
    ({'x': 1, 'y': 20, 'price': 10}, 7.482029277778401),
    ({'x': 1, 'y': 20, 'price': 15}, 13.223192267466496),
    ({'x': 1, 'y': 20, 'price': 30}, 8.63950323522004),
    ({'x': 1, 'y': 20, 'price': 31}, 8.63950323522004),
    ({'x': 10, 'y': 0, 'price': 9}, 74.820292777784),
    ({'x': 10, 'y': 0, 'price': 10}, 74.820292777784),
    ({'x': 10, 'y': 0, 'price': 15}, 0.0),
    ({'x': 10, 'y': 0, 'price': 30}, 0.0),
    ({'x': 10, 'y': 0, 'price': 31}, 0.0),
    ({'x': 10, 'y': 2, 'price': 9}, 74.820292777784),
    ({'x': 10, 'y': 2, 'price': 10}, 74.820292777784),
    ({'x': 10, 'y': 2, 'price': 15}, 2.814104402550319),
    ({'x': 10, 'y': 2, 'price': 30}, 0.8639503235220041),
    ({'x': 10, 'y': 2, 'price': 31}, 0.8639503235220041),
    ({'x': 10, 'y': 20, 'price': 9}, 74.820292777784),
    ({'x': 10, 'y': 20, 'price': 10}, 74.820292777784),
    ({'x': 10, 'y': 20, 'price': 15}, 28.141044025503188),
    ({'x': 10, 'y': 20, 'price': 30}, 8.63950323522004),
    ({'x': 10, 'y': 20, 'price': 31}, 8.63950323522004)
]


test_liq_to_optimal_xy_arr = [
    ({'price': 9, 'liq': 0}, (0.0, 0)),
    ({'price': 10, 'liq': 0}, (0.0, 0)),
    ({'price': 20, 'liq': 0}, (0.0, 0.0)),
    ({'price': 30, 'liq': 0}, (0, 0.0)),
    ({'price': 31, 'liq': 0}, (0, 0.0)),
    ({'price': 9, 'liq': 10}, (1.3365358018178255, 0)),
    ({'price': 10, 'liq': 10}, (1.3365358018178255, 0)),
    ({'price': 20, 'liq': 10}, (0.4103261191492359, 13.098582948312)),
    ({'price': 30, 'liq': 10}, (0, 23.149479148832818)),
    ({'price': 31, 'liq': 10}, (0, 23.149479148832818)),
    ({'price': 9, 'liq': 20}, (2.673071603635651, 0)),
    ({'price': 10, 'liq': 20}, (2.673071603635651, 0)),
    ({'price': 20, 'liq': 20}, (0.8206522382984718, 26.197165896624)),
    ({'price': 30, 'liq': 20}, (0, 46.298958297665635)),
    ({'price': 31, 'liq': 20}, (0, 46.298958297665635))
]


test_check_xy_is_optimal_arr = [
    ({'x': 0, 'y': 0, 'price': 9}, (True, 0.0, 0.0)),
    ({'x': 0, 'y': 0, 'price': 10}, (True, 0.0, 0.0)),
    ({'x': 0, 'y': 0, 'price': 15}, (True, 0.0, 0.0)),
    ({'x': 0, 'y': 0, 'price': 30}, (True, 0.0, 0.0)),
    ({'x': 0, 'y': 0, 'price': 31}, (True, 0.0, 0.0)),
    ({'x': 0, 'y': 2, 'price': 9}, (False, 0.0, 0.0)),
    ({'x': 0, 'y': 2, 'price': 10}, (False, 0.0, 0.0)),
    ({'x': 0, 'y': 2, 'price': 15}, (False, 0.0, 2.814104402550319)),
    ({'x': 0, 'y': 2, 'price': 30}, (True, 0.0, 0.8639503235220041)),
    ({'x': 0, 'y': 2, 'price': 31}, (True, 0.0, 0.8639503235220041)),
    ({'x': 0, 'y': 20, 'price': 9}, (False, 0.0, 0.0)),
    ({'x': 0, 'y': 20, 'price': 10}, (False, 0.0, 0.0)),
    ({'x': 0, 'y': 20, 'price': 15}, (False, 0.0, 28.141044025503188)),
    ({'x': 0, 'y': 20, 'price': 30}, (True, 0.0, 8.63950323522004)),
    ({'x': 0, 'y': 20, 'price': 31}, (True, 0.0, 8.63950323522004)),
    ({'x': 1, 'y': 0, 'price': 9}, (True, 7.482029277778401, 0.0)),
    ({'x': 1, 'y': 0, 'price': 10}, (True, 7.482029277778401, 0.0)),
    ({'x': 1, 'y': 0, 'price': 15}, (False, 13.223192267466496, 0.0)),
    ({'x': 1, 'y': 0, 'price': 30}, (False, 0.0, 0.0)),
    ({'x': 1, 'y': 0, 'price': 31}, (False, 0.0, 0.0)),
    ({'x': 1, 'y': 2, 'price': 9}, (False, 7.482029277778401, 0.0)),
    ({'x': 1, 'y': 2, 'price': 10}, (False, 7.482029277778401, 0.0)),
    ({'x': 1, 'y': 2, 'price': 15}, (False, 13.223192267466496, 2.814104402550319)),
    ({'x': 1, 'y': 2, 'price': 30}, (False, 0.0, 0.8639503235220041)),
    ({'x': 1, 'y': 2, 'price': 31}, (False, 0.0, 0.8639503235220041)),
    ({'x': 1, 'y': 20, 'price': 9}, (False, 7.482029277778401, 0.0)),
    ({'x': 1, 'y': 20, 'price': 10}, (False, 7.482029277778401, 0.0)),
    ({'x': 1, 'y': 20, 'price': 15}, (False, 13.223192267466496, 28.141044025503188)),
    ({'x': 1, 'y': 20, 'price': 30}, (False, 0.0, 8.63950323522004)),
    ({'x': 1, 'y': 20, 'price': 31}, (False, 0.0, 8.63950323522004)),
    ({'x': 10, 'y': 0, 'price': 9}, (True, 74.820292777784, 0.0)),
    ({'x': 10, 'y': 0, 'price': 10}, (True, 74.820292777784, 0.0)),
    ({'x': 10, 'y': 0, 'price': 15}, (False, 132.23192267466496, 0.0)),
    ({'x': 10, 'y': 0, 'price': 30}, (False, 0.0, 0.0)),
    ({'x': 10, 'y': 0, 'price': 31}, (False, 0.0, 0.0)),
    ({'x': 10, 'y': 2, 'price': 9}, (False, 74.820292777784, 0.0)),
    ({'x': 10, 'y': 2, 'price': 10}, (False, 74.820292777784, 0.0)),
    ({'x': 10, 'y': 2, 'price': 15}, (False, 132.23192267466496, 2.814104402550319)),
    ({'x': 10, 'y': 2, 'price': 30}, (False, 0.0, 0.8639503235220041)),
    ({'x': 10, 'y': 2, 'price': 31}, (False, 0.0, 0.8639503235220041)),
    ({'x': 10, 'y': 20, 'price': 9}, (False, 74.820292777784, 0.0)),
    ({'x': 10, 'y': 20, 'price': 10}, (False, 74.820292777784, 0.0)),
    ({'x': 10, 'y': 20, 'price': 15}, (False, 132.23192267466496, 28.141044025503188)),
    ({'x': 10, 'y': 20, 'price': 30}, (False, 0.0, 8.63950323522004)),
    ({'x': 10, 'y': 20, 'price': 31}, (False, 0.0, 8.63950323522004)),
    ({'x': 3.327228186386449, 'y': 82.03034145444167, 'price': 18.842184491108632}, (True, 69.60685111982906, 69.60685111982906)),
    ({'x': 0.8443499732404194, 'y': 73.33550152458729, 'price': 24.288590089009084}, (True, 41.52473468483802, 41.52473468483802)),
    ({'x': 5.118156689584054, 'y': 37.26100105401416, 'price': 14.183932574326864}, (True, 61.702806399273214, 61.702806399273214)),
    ({'x': 0.6419037100664964, 'y': 177.2725013645119, 'price': 27.652798298426482}, (True, 84.5638604119948, 84.5638604119948)),
    ({'x': 1.9161783114501243, 'y': 71.8423822551345, 'price': 20.72590821206501}, (True, 51.674239508552226, 51.674239508552226))
]

test_get_amounts_after_optimal_swap_arr = [
    ({'x': 0, 'y': 0, 'price': 9, 'swap_fee': 0}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 9, 'swap_fee': 0}, (0.1111111111111111, 0)),
    ({'x': 0, 'y': 3, 'price': 9, 'swap_fee': 0}, (0.3333333333333333, 0)),
    ({'x': 1, 'y': 0, 'price': 9, 'swap_fee': 0}, (1.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 9, 'swap_fee': 0}, (1.1111111111111112, 0)),
    ({'x': 1, 'y': 3, 'price': 9, 'swap_fee': 0}, (1.3333333333333333, 0)),
    ({'x': 15, 'y': 0, 'price': 9, 'swap_fee': 0}, (15.0, 0.0)),
    ({'x': 15, 'y': 1, 'price': 9, 'swap_fee': 0}, (15.11111111111111, 0)),
    ({'x': 15, 'y': 3, 'price': 9, 'swap_fee': 0}, (15.333333333333334, 0)),
    ({'x': 0, 'y': 0, 'price': 9, 'swap_fee': 0.1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 9, 'swap_fee': 0.1}, (0.1, 0.0)),
    ({'x': 0, 'y': 3, 'price': 9, 'swap_fee': 0.1}, (0.30000000000000004, 0.0)),
    ({'x': 1, 'y': 0, 'price': 9, 'swap_fee': 0.1}, (1.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 9, 'swap_fee': 0.1}, (1.1, 0.0)),
    ({'x': 1, 'y': 3, 'price': 9, 'swap_fee': 0.1}, (1.3, 0.0)),
    ({'x': 15, 'y': 0, 'price': 9, 'swap_fee': 0.1}, (15.0, 0.0)),
    ({'x': 15, 'y': 1, 'price': 9, 'swap_fee': 0.1}, (15.1, 0.0)),
    ({'x': 15, 'y': 3, 'price': 9, 'swap_fee': 0.1}, (15.3, 0.0)),
    ({'x': 0, 'y': 0, 'price': 9, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 9, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 0, 'y': 3, 'price': 9, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 1, 'y': 0, 'price': 9, 'swap_fee': 1}, (1.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 9, 'swap_fee': 1}, (1.0, 0)),
    ({'x': 1, 'y': 3, 'price': 9, 'swap_fee': 1}, (1.0, 0)),
    ({'x': 15, 'y': 0, 'price': 9, 'swap_fee': 1}, (15.0, 0.0)),
    ({'x': 15, 'y': 1, 'price': 9, 'swap_fee': 1}, (15.0, 0)),
    ({'x': 15, 'y': 3, 'price': 9, 'swap_fee': 1}, (15.0, 0)),
    ({'x': 0, 'y': 0, 'price': 10, 'swap_fee': 0}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 10, 'swap_fee': 0}, (0.1, 0)),
    ({'x': 0, 'y': 3, 'price': 10, 'swap_fee': 0}, (0.3, 0)),
    ({'x': 1, 'y': 0, 'price': 10, 'swap_fee': 0}, (1.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 10, 'swap_fee': 0}, (1.1, 0)),
    ({'x': 1, 'y': 3, 'price': 10, 'swap_fee': 0}, (1.3, 0)),
    ({'x': 15, 'y': 0, 'price': 10, 'swap_fee': 0}, (15.0, 0.0)),
    ({'x': 15, 'y': 1, 'price': 10, 'swap_fee': 0}, (15.1, 0)),
    ({'x': 15, 'y': 3, 'price': 10, 'swap_fee': 0}, (15.3, 0)),
    ({'x': 0, 'y': 0, 'price': 10, 'swap_fee': 0.1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 10, 'swap_fee': 0.1}, (0.09, 0.0)),
    ({'x': 0, 'y': 3, 'price': 10, 'swap_fee': 0.1}, (0.27, 0.0)),
    ({'x': 1, 'y': 0, 'price': 10, 'swap_fee': 0.1}, (1.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 10, 'swap_fee': 0.1}, (1.09, 0.0)),
    ({'x': 1, 'y': 3, 'price': 10, 'swap_fee': 0.1}, (1.27, 0.0)),
    ({'x': 15, 'y': 0, 'price': 10, 'swap_fee': 0.1}, (15.0, 0.0)),
    ({'x': 15, 'y': 1, 'price': 10, 'swap_fee': 0.1}, (15.09, 0.0)),
    ({'x': 15, 'y': 3, 'price': 10, 'swap_fee': 0.1}, (15.27, 0.0)),
    ({'x': 0, 'y': 0, 'price': 10, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 10, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 0, 'y': 3, 'price': 10, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 1, 'y': 0, 'price': 10, 'swap_fee': 1}, (1.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 10, 'swap_fee': 1}, (1.0, 0)),
    ({'x': 1, 'y': 3, 'price': 10, 'swap_fee': 1}, (1.0, 0)),
    ({'x': 15, 'y': 0, 'price': 10, 'swap_fee': 1}, (15.0, 0.0)),
    ({'x': 15, 'y': 1, 'price': 10, 'swap_fee': 1}, (15.0, 0)),
    ({'x': 15, 'y': 3, 'price': 10, 'swap_fee': 1}, (15.0, 0)),
    ({'x': 0, 'y': 0, 'price': 14, 'swap_fee': 0}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 14, 'swap_fee': 0},
     (0.04798137534764351, 0.32826074513299086)),
    ({'x': 0, 'y': 3, 'price': 14, 'swap_fee': 0},
     (0.14394412604293055, 0.9847822353989724)),
    ({'x': 1, 'y': 0, 'price': 14, 'swap_fee': 0},
     (0.6717392548670091, 4.595650431861872)),
    ({'x': 1, 'y': 1, 'price': 14, 'swap_fee': 0},
     (0.7197206302146526, 4.923911176994863)),
    ({'x': 1, 'y': 3, 'price': 14, 'swap_fee': 0},
     (0.8156833809099396, 5.580432667260845)),
    ({'x': 15, 'y': 0, 'price': 14, 'swap_fee': 0},
     (10.076088823005136, 68.93475647792808)),
    ({'x': 15, 'y': 1, 'price': 14, 'swap_fee': 0},
     (10.124070198352783, 69.26301722306106)),
    ({'x': 15, 'y': 3, 'price': 14, 'swap_fee': 0},
     (10.220032949048068, 69.91953871332704)),
    ({'x': 0, 'y': 0, 'price': 14, 'swap_fee': 0.1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 14, 'swap_fee': 0.1},
     (0.04464888545371869, 0.30546178183104267)),
    ({'x': 0, 'y': 3, 'price': 14, 'swap_fee': 0.1},
     (0.13394665636115607, 0.9163853454931279)),
    ({'x': 1, 'y': 0, 'price': 14, 'swap_fee': 0.1},
     (0.6481008045317981, 4.433929862899345)),
    ({'x': 1, 'y': 1, 'price': 14, 'swap_fee': 0.1},
     (0.6995373763200361, 4.785829058367546)),
    ({'x': 1, 'y': 3, 'price': 14, 'swap_fee': 0.1},
     (0.8024105198965119, 5.489627449303949)),
    ({'x': 15, 'y': 0, 'price': 14, 'swap_fee': 0.1},
     (9.721512067976972, 66.50894794349016)),
    ({'x': 15, 'y': 1, 'price': 14, 'swap_fee': 0.1},
     (9.772948639765211, 66.86084713895835)),
    ({'x': 15, 'y': 3, 'price': 14, 'swap_fee': 0.1},
     (9.875821783341685, 67.56464552989476)),
    ({'x': 0, 'y': 0, 'price': 14, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 14, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 0, 'y': 3, 'price': 14, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 1, 'y': 0, 'price': 14, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 1, 'y': 1, 'price': 14, 'swap_fee': 1}, (0.14616848361872947, 1.0)),
    ({'x': 1, 'y': 3, 'price': 14, 'swap_fee': 1}, (0.4385054508561884, 3.0)),
    ({'x': 15, 'y': 0, 'price': 14, 'swap_fee': 1},
     (1.7763568394002505e-15, 0.0)),
    ({'x': 15, 'y': 1, 'price': 14, 'swap_fee': 1}, (0.14616848361873203, 1.0)),
    ({'x': 15, 'y': 3, 'price': 14, 'swap_fee': 1}, (0.43850545085619075, 3.0)),
    ({'x': 0, 'y': 0, 'price': 30, 'swap_fee': 0}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 30, 'swap_fee': 0}, (0.0, 1.0)),
    ({'x': 0, 'y': 3, 'price': 30, 'swap_fee': 0}, (0.0, 3.0)),
    ({'x': 1, 'y': 0, 'price': 30, 'swap_fee': 0}, (0.0, 30)),
    ({'x': 1, 'y': 1, 'price': 30, 'swap_fee': 0}, (0.0, 31)),
    ({'x': 1, 'y': 3, 'price': 30, 'swap_fee': 0}, (0.0, 33)),
    ({'x': 15, 'y': 0, 'price': 30, 'swap_fee': 0}, (0.0, 450)),
    ({'x': 15, 'y': 1, 'price': 30, 'swap_fee': 0}, (0.0, 451)),
    ({'x': 15, 'y': 3, 'price': 30, 'swap_fee': 0}, (0.0, 453)),
    ({'x': 0, 'y': 0, 'price': 30, 'swap_fee': 0.1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 30, 'swap_fee': 0.1}, (0.0, 1.0)),
    ({'x': 0, 'y': 3, 'price': 30, 'swap_fee': 0.1}, (0.0, 3.0)),
    ({'x': 1, 'y': 0, 'price': 30, 'swap_fee': 0.1}, (0.0, 27.0)),
    ({'x': 1, 'y': 1, 'price': 30, 'swap_fee': 0.1}, (0.0, 28.0)),
    ({'x': 1, 'y': 3, 'price': 30, 'swap_fee': 0.1}, (0.0, 30.0)),
    ({'x': 15, 'y': 0, 'price': 30, 'swap_fee': 0.1}, (0.0, 405.0)),
    ({'x': 15, 'y': 1, 'price': 30, 'swap_fee': 0.1}, (0.0, 406.0)),
    ({'x': 15, 'y': 3, 'price': 30, 'swap_fee': 0.1}, (0.0, 408.0)),
    ({'x': 0, 'y': 0, 'price': 30, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 30, 'swap_fee': 1}, (0.0, 1.0)),
    ({'x': 0, 'y': 3, 'price': 30, 'swap_fee': 1}, (0.0, 3.0)),
    ({'x': 1, 'y': 0, 'price': 30, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 1, 'y': 1, 'price': 30, 'swap_fee': 1}, (0.0, 1)),
    ({'x': 1, 'y': 3, 'price': 30, 'swap_fee': 1}, (0.0, 3)),
    ({'x': 15, 'y': 0, 'price': 30, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 15, 'y': 1, 'price': 30, 'swap_fee': 1}, (0.0, 1)),
    ({'x': 15, 'y': 3, 'price': 30, 'swap_fee': 1}, (0.0, 3)),
    ({'x': 0, 'y': 0, 'price': 31, 'swap_fee': 0}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 31, 'swap_fee': 0}, (0.0, 1.0)),
    ({'x': 0, 'y': 3, 'price': 31, 'swap_fee': 0}, (0.0, 3.0)),
    ({'x': 1, 'y': 0, 'price': 31, 'swap_fee': 0}, (0.0, 31)),
    ({'x': 1, 'y': 1, 'price': 31, 'swap_fee': 0}, (0.0, 32)),
    ({'x': 1, 'y': 3, 'price': 31, 'swap_fee': 0}, (0.0, 34)),
    ({'x': 15, 'y': 0, 'price': 31, 'swap_fee': 0}, (0.0, 465)),
    ({'x': 15, 'y': 1, 'price': 31, 'swap_fee': 0}, (0.0, 466)),
    ({'x': 15, 'y': 3, 'price': 31, 'swap_fee': 0}, (0.0, 468)),
    ({'x': 0, 'y': 0, 'price': 31, 'swap_fee': 0.1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 31, 'swap_fee': 0.1}, (0.0, 1.0)),
    ({'x': 0, 'y': 3, 'price': 31, 'swap_fee': 0.1}, (0.0, 3.0)),
    ({'x': 1, 'y': 0, 'price': 31, 'swap_fee': 0.1}, (0.0, 27.900000000000002)),
    ({'x': 1, 'y': 1, 'price': 31, 'swap_fee': 0.1}, (0.0, 28.900000000000002)),
    ({'x': 1, 'y': 3, 'price': 31, 'swap_fee': 0.1}, (0.0, 30.900000000000002)),
    ({'x': 15, 'y': 0, 'price': 31, 'swap_fee': 0.1}, (0.0, 418.5)),
    ({'x': 15, 'y': 1, 'price': 31, 'swap_fee': 0.1}, (0.0, 419.5)),
    ({'x': 15, 'y': 3, 'price': 31, 'swap_fee': 0.1}, (0.0, 421.5)),
    ({'x': 0, 'y': 0, 'price': 31, 'swap_fee': 1}, (0.0, 0.0)),
    ({'x': 0, 'y': 1, 'price': 31, 'swap_fee': 1}, (0.0, 1.0)),
    ({'x': 0, 'y': 3, 'price': 31, 'swap_fee': 1}, (0.0, 3.0)),
    ({'x': 1, 'y': 0, 'price': 31, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 1, 'y': 1, 'price': 31, 'swap_fee': 1}, (0.0, 1)),
    ({'x': 1, 'y': 3, 'price': 31, 'swap_fee': 1}, (0.0, 3)),
    ({'x': 15, 'y': 0, 'price': 31, 'swap_fee': 1}, (0.0, 0)),
    ({'x': 15, 'y': 1, 'price': 31, 'swap_fee': 1}, (0.0, 1)),
    ({'x': 15, 'y': 3, 'price': 31, 'swap_fee': 1}, (0.0, 3))
]

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
        # all works, leave it here just in case
        # sys.stdout.write('\n\n\nssssss\n\n\n')

        ans = self.aligner.xy_to_liq(**input_val)

        self.assertTrue(np.allclose(ans, expected, atol=1e-08, rtol=0))

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

        ans = UniswapLiquidityAligner(10, 30).liq_to_xy(**input_val)

        self.assertTrue(np.allclose(ans, expected, atol=1e-8, rtol=0))

    def test_liq_to_optimal_xy_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.liq_to_xy(price=0, liq=1)
        self.assertTrue('Incorrect price' in str(context.exception))

    def test_liq_to_optimal_xy_assert_liquidity(self):
        with self.assertRaises(Exception) as context:
            self.aligner.liq_to_xy(price=1, liq=-1)
        self.assertTrue('Incorrect liquidity' in str(context.exception))

    @parameterized.expand(test_check_xy_is_optimal_arr)
    def test_check_xy_is_optimal(self, input_val, expected):
        """
            run test
        Returns:
        """

        ans = UniswapLiquidityAligner(10, 30).check_xy_is_optimal(**input_val)

        self.assertTrue(np.allclose(ans, expected, atol=1e-8, rtol=0))

    def test_check_xy_is_optimal_assert_price(self):
        with self.assertRaises(Exception) as context:
            self.aligner.check_xy_is_optimal(price=-1, x=1, y=1)
        self.assertTrue('Incorrect price' in str(context.exception))

    def test_check_xy_is_optimal_assert_x(self):
        with self.assertRaises(Exception) as context:
            self.aligner.check_xy_is_optimal(price=1, x=-1, y=1)
        self.assertTrue('Incorrect x' in str(context.exception))

    def test_check_xy_is_optimal_assert_y(self):
        with self.assertRaises(Exception) as context:
            self.aligner.xy_to_liq(price=1, x=1, y=-1)
        self.assertTrue('Incorrect y' in str(context.exception))

    @parameterized.expand(test_get_amounts_after_optimal_swap_arr)
    def test_get_amounts_after_optimal_swap(self, input_val, expected):
        """
            run test
        Returns:
        """

        ans = UniswapLiquidityAligner(10, 30).get_amounts_after_optimal_swap(**input_val)

        self.assertTrue(np.allclose(ans, expected, atol=1e-8, rtol=0))

if __name__ == "__main__":
    unittest.main()
