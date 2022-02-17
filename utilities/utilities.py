"""
TODO write
"""
import sys
import os
import yaml
from sqlalchemy import create_engine


class ConfigParser:
    """
        parse yml config to python dict
    """
    def __init__(self):
        add_main_path()
        self.path = os.path.join(get_main_path(), "configs", "config.yml")

        with open(self.path, 'r') as stream:
            self.config = yaml.safe_load(stream)


def get_db_connector():
    """
        create connector for using pd.read_sql_query
    Args:
        path_to_config:
    Returns:
        connector :)
    """
    parser = ConfigParser()
    return create_engine(
        "mysql+pymysql://{user}:{password}@{host}/{db}".format(
            user=parser.config['db_config']['user'],
            password=parser.config['db_config']['password'],
            host=parser.config['db_config']['host'],
            db=parser.config['db_config']['db']
        )
    )


def add_main_path():
    """
         add the path to the main directory ../mellow-strategy-sdk
    Returns:
        None
    """
    current_path = os.getcwd()
    while current_path:
        if os.path.split(current_path)[1] == 'mellow-strategy-sdk':
            sys.path.append(current_path)
            break
        current_path = os.path.split(current_path)[0]


def get_main_path():
    """
         get the path of the main directory ../mellow-strategy-sdk
    Returns:
        None
    """
    current_path = os.getcwd()
    while current_path:
        if os.path.split(current_path)[1] == 'mellow-strategy-sdk':
            return current_path
        current_path = os.path.split(current_path)[0]
