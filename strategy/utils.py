"""
    file with helper functions
"""

import os
from pathlib import Path
import yaml


from sqlalchemy import create_engine


ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = os.path.join(ROOT_DIR, 'configs/config.yml')
DATA_DIR = os.path.join(ROOT_DIR, 'data')


class ConfigParser:
    """
        Parse yml config configs/config.yml to python dict
    """
    def __init__(self, config_path):
        self.path = config_path

        with open(self.path, 'r') as stream:
            self.config = yaml.safe_load(stream)


def get_db_connector(config_path):
    """
        Create db connector for using pd.read_sql_query

    Returns:
        result of sqlalchemy.create_engine
    """
    config = ConfigParser(config_path=config_path).config
    return create_engine(
        "mysql+pymysql://{user}:{password}@{host}/{db}".format(
            user=config['db_config']['user'],
            password=config['db_config']['password'],
            host=config['db_config']['host'],
            db=config['db_config']['db']
        )
    )

