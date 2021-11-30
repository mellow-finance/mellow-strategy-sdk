import copy
import numpy as np
import pandas as pd
from multiprocessing import Pool

from .Backtest import Backtest


class FolderSimple:
    """
       ``FolderSimple`` makes the splitting into equal folds.
       :param n_folds: Number of folds.
   """
    def __init__(self,
                 n_folds: int = 5,
                 ):

        self.n_folds = n_folds
        self.folds = None
        self.fold_names = None

    def generate_folds_by_index(self, data):
        """
        Split data into folds
        :param data: Uniswap exchancge data
        """
        index = np.sort(data.index.to_numpy())
        n = len(index)
        fold_len = n // self.n_folds

        idx_split = [i * fold_len for i in range(self.n_folds + 1)]
        if idx_split[-1] != n:
            idx_split[-1] = nRun backtest on data

        folds = {}
        for i, j in enumerate(range(len(idx_split)-1)):
            folds[f'fold_{i + 1}'] = index[idx_split[j]:idx_split[j+1]]

        self.folds = folds
        self.fold_names = list(folds.keys())
        return None

    def get_fold(self, data, fold_name):
        """
        Get fold by name
        :param data: Uniswap exchancge data
        :param fold_name: Folds name
        :return: Folds data as PoolDataUniV3
        """
        fold_idx = self.folds[fold_name]
        fold_data = data.loc[data.index.isin(fold_idx)]
        return fold_data


class CrossValidation:
    """
       ``CrossValidation`` backtests strategy on folds.
       :param folder: Folder class that splits data on folds
       :param strategy: Strategy to backtest
   """
    def __init__(self, folder, strategy):
        self.folder = folder
        self.strategy = strategy

    def _backtest_(self, *args):
        """
        Run backtest on single fold
        :param args[0]: Uniswap exchancge data
        :param args[1]: Folds name
        :return: Dict of history results
        """
        data, fold_name = args[0][0], args[0][1]
        backtest = Backtest(self.strategy)
        fold_data = self.folder.get_fold(data.swaps, fold_name)
        portfolio_history, rebalance_history, uni_history = backtest.backtest(fold_data)
        res = {'portfolio': portfolio_history,
                'rebalance': rebalance_history,
                'uniswap': uni_history}
        return res

    def backtest(self, data):
        """
        Parallel backtesting on folded data
        :param data: Uniswap exchancge data
        :return: List of history dicts by folds
        """
        self.folder.generate_folds_by_index(data.swaps)
        args = [(data, fold_name) for fold_name in self.folder.fold_names]
        with Pool(processes=len(self.folder.fold_names)) as pool:
            folds_result = pool.map(self. _backtest_, args)

        # for fold_name in self.folder.fold_names:
        #    res = self. _backtest_(data, fold_name)
        #    folds_result[fold_name] = res
        return folds_result

    def aggregate(self, folds_result):
        """
        Aggregate backtesting results from folds
        :param folds_result: History from folds
        :return: Dict of APY's by folds
        """
        res = {}
        for k, v in folds_result.items():
            df = v['portfolio'].portfolio_stats()
            res[k] = df.iloc[-1]['portfolio_performance_to_y_to_year']

        res_df = pd.DataFrame([res], index=['y_apy']).T
        return res_df


# class FolderByTime:
#     def __init__(self,
#                  n_folds: int = 5,
#                  seed: int = 4242,
#                  ):
#
#         self.n_folds = n_folds
#         self.seed = seed
#         self.folds = None
#         self.fold_names = None
#
#     def generate_folds_by_index(self, data):
#         index = data.index
#         values = np.sort(index.to_numpy())
#         folder = TimeSeriesSplit(n_splits=self.n_folds)
#
#         folds = {}
#         for i, (train_idx, valid_idx) in enumerate(folder.split(values)):
#             folds[f'fold_{i + 1}'] = {'train': index[train_idx], 'valid': index[valid_idx]}
#
#         self.folds = folds
#         self.fold_names = list(folds.keys())
#         # return folds
#
#     def get_fold(self, data, fold_name):
#         fold_idx = self.folds[fold_name]
#         train_data = data.loc[data.index.isin(fold_idx['train'])]
#         valid_data = data.loc[data.index.isin(fold_idx['valid'])]
#         fold_data = {'train': train_data, 'valid': valid_data}
#         return fold_data
