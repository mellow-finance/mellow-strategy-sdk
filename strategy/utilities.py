"""
    file with helper functions
"""
import sys
import os
from datetime import datetime
import yaml
import pandas as pd
import numpy as np
import subprocess

from sqlalchemy import create_engine
from binance import Client


class ConfigParser:
    """
        Parse yml config configs/config.yml to python dict
    """
    def __init__(self):
        add_main_path()
        self.path = os.path.join(get_main_path(), "configs", "config.yml")

        with open(self.path, 'r') as stream:
            self.config = yaml.safe_load(stream)


def get_db_connector():
    """
        Create db connector for using pd.read_sql_query

    Returns:
        result of sqlalchemy.create_engine
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


def add_main_path() -> None:
    """
        Add the path to the main directory ../mellow-strategy-sdk in sys.path

    Returns:
    """
    current_path = os.getcwd()
    while current_path:
        if os.path.split(current_path)[1] == 'mellow-strategy-sdk':
            sys.path.append(current_path)
            break
        current_path = os.path.split(current_path)[0]


def get_main_path():
    """
    Returns:
        path of the main directory ../mellow-strategy-sdk
    """
    current_path = os.getcwd()
    while current_path:
        if os.path.split(current_path)[1] == 'mellow-strategy-sdk':
            return current_path
        current_path = os.path.split(current_path)[0]


# Note
# get_historical_klines
# [
#   [
#     1499040000000,      // Open time - 0
#     "0.01634790",       // Open
#     "0.80000000",       // High
#     "0.01575800",       // Low
#     "0.01577100",       // Close - 4
#     "148976.11427815",  // Volume
#     1499644799999,      // Close time
#     "2434.19055334",    // Quote asset volume
#     308,                // Number of trades
#     "1756.87402397",    // Taker buy base asset volume
#     "28.46694368",      // Taker buy quote asset volume
#     "17928899.62484339" // Ignore
#   ]
# ]

def get_data_from_binance(pair_name, interval, start_str, end_str) -> pd.DataFrame:
    """
        Download pair data from binance and write csv to /data folder.
    Args:
        pair_name: 'ethusdc' or other
        interval: Binance interval string, e.g.:
            '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w'
        start_str: string in format '%d-%M-%Y' (utc time format), (example '05-12-2018')
        end_str: string in format '%d-%M-%Y' (utc time format)
    Returns:
        pandas dataframe that was written to the /data/f'{pair_name}_{interval}_{start_str}_{end_str}.csv'
    """
    # in - ms
    # in * 1000 - us
    pair_name = str.upper(pair_name)
    # we need to get the num of sec in the interval
    map_dict = {'m': 1, 'h': 60, 'd': 24 * 60, 'w': 7 * 24 * 60}
    # num of nano sec [us]
    us_num = int(interval[0:-1]) * map_dict[interval[-1]] * 60 * 1000 * 1000

    # binance api client
    client = Client(
        ConfigParser().config['binance']['api_key'],
        ConfigParser().config['binance']['api_secret']
    )

    # download candles
    print('start:', datetime.now())
    try:
        klines = client.get_historical_klines(
            symbol=pair_name,
            interval=interval,
            start_str=start_str,
            end_str=end_str
        )
    except:
        assert False, 'using the api failed'
    print('finish:', datetime.now())
    print('rows downloaded:', len(klines))
    assert len(klines) > 1, '0 or 1 rows downloaded!'

    # preparing to timestamp to nano sec datetime[us]
    ts = [i[0] * 1000 for i in klines]
    index_col = list(range(ts[0], ts[-1] + us_num, us_num))

    # convert price to float
    price_col = [float(i[4]) for i in klines]

    # create dataframe
    df = pd.DataFrame({'price': [np.nan]}, index=index_col)
    df.index.name = 'timestamp'

    mismatch_rows = list(set(ts) - set(index_col))
    print('mismatch timestamp rows: ', len(mismatch_rows))

    data = np.array([ts, price_col])
    data = data[:, np.isin(data[0, :], mismatch_rows, invert=True)]

    df.loc[data[0, :], 'price'] = data[1, :]
    df.index = pd.to_datetime(df.index, unit='us')

    df['price'] = df['price'].shift(1)
    df = df.iloc[1:]
    df = df.reset_index()

    root = get_main_path()
    file_name = f'{pair_name}_{interval}_{start_str}_{end_str}.csv'
    file_path = os.path.join(root, 'data', file_name)

    subprocess.run(['mkdir', '-p', os.path.join(root, 'data')])
    df.to_csv(file_path, index=False, date_format='%Y-%m-%d %H:%M:%S:%f')
    print(f'df shape {df.shape} saved to {file_path}')
    return df
