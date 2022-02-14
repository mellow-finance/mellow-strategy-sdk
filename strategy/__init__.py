import os
import sys

if os.path.split(os.getcwd())[0] not in sys.path:
    sys.path.append(os.path.split(os.getcwd())[0])

from .Backtest import Backtest