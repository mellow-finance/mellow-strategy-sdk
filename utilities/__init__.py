"""
    lib with minor helper functions and classes
"""

import sys
import os

if os.path.split(os.getcwd())[0] not in sys.path:
    sys.path.append(os.path.split(os.getcwd())[0])

import yaml
from .utilities import ConfigParser, get_db_connector, add_main_path, get_main_path


# add_main_path() # add mellow-strategy-sdk in sys.path
# print(os.path.dirname(__file__)) # gives the path to this directory .../utilities


