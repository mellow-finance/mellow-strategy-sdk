"""
    file with helper functions
"""

import os
from pathlib import Path
import yaml
import structlog


ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = os.path.join(ROOT_DIR, 'configs/config.yml')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

log = structlog.get_logger()


class ConfigParser:
    """
        Parse yml config configs/config.yml to python dict
    """
    def __init__(self, config_path):
        self.path = config_path

        with open(self.path, 'r') as stream:
            self.config = yaml.safe_load(stream)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AtomicSnapshot(metaclass=Singleton):
    def __init__(self):
        self.snapshots = []
        self.timestamp = None
        self.price = None
        self.portfolio = None

    def __call__(self, func):

        def wrapper(obj, *args, **kwargs):
            # snapshot = {'timestamp': self.timestamp, 'price': self.price}
            snapshot = self.portfolio.snapshot(timestamp=self.timestamp, price=self.price)
            self.snapshots.append(snapshot)

            # snapshot.update(
            #     **obj.snapshot(timestamp=self.timestamp, price=self.price)
            # )
            # self.snapshots.append(snapshot)
            return func(obj, *args, **kwargs)

        return wrapper