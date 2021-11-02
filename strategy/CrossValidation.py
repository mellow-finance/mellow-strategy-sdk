import copy
import numpy as np
from sklearn.model_selection import TimeSeriesSplit

from .Backtest import Backtest


class FolderSimple:
    def __init__(self,
                 n_folds: int = 5,
                 seed: int = 4242,
                 ):

        self.n_folds = n_folds
        self.seed = seed
        self.folds = None
        self.fold_names = None

    def generate_folds_by_index(self, data):
        index = np.sort(data.index.to_numpy())
        n = len(index)
        fold_len = n // self.n_folds
        idx_split = [i * fold_len for i in range(self.n_folds + 1)]
        if idx_split[-1] != n:
            idx_split[-1] = n

        folds = {}
        for i, j in enumerate(range(len(idx_split)-1)):
            folds[f'fold_{i + 1}'] = index[idx_split[j]:idx_split[j+1]]

        self.folds = folds
        self.fold_names = list(folds.keys())
        return None

    def get_fold(self, data, fold_name):
        fold_idx = self.folds[fold_name]
        fold_data = data.loc[data.index.isin(fold_idx)]
        return fold_data


class CrossValidation:
    def __init__(self, folder, strategy):
        self.folder = folder
        self.strategy = strategy

    def backtest(self, data):
        folds_result = {}
        self.folder.generate_folds_by_index(data.swaps)
        for fold_name in self.folder.fold_names:
            backtest = Backtest(self.strategy)
            fold_data = self.folder.get_fold(data.swaps, fold_name)
            backtest_history = backtest.backtest(fold_data)
            folds_result[fold_name] = backtest_history
        return folds_result


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