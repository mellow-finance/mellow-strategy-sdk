"""
    lib with minor helper functions and classes
"""

import sys
import os
import yaml

if os.path.split(os.getcwd())[0] not in sys.path:
    sys.path.append(os.path.split(os.getcwd())[0])


# TODO вроде в новом питоне можно удалить
from .utilities import ConfigParser, get_db_connector, add_main_path, get_main_path

