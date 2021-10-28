from sklearn.model_selection import KFold, train_test_split, TimeSeriesSplit
import pandas as pd
import numpy as np
import copy

from .Backtest import Backtest


class FolderByTime:
    def __init__(self,
                 n_folds: int = 5,
                 seed: int = 4242,
                 ):

        self.n_folds = n_folds
        self.seed = seed
        self.folds = None
        self.fold_names = None

    def generate_folds_by_index(self, data):
        index = data.index
        values = np.sort(index.to_numpy())
        folder = TimeSeriesSplit(n_splits=self.n_folds)

        folds = {}
        for i, (train_idx, valid_idx) in enumerate(folder.split(values)):
            folds[f'fold_{i + 1}'] = {'train': index[train_idx], 'valid': index[valid_idx]}

        self.folds = folds
        self.fold_names = list(folds.keys())
        # return folds

    def get_fold(self, data, fold_name):
        fold_idx = self.folds[fold_name]
        train_data = data.loc[data.index.isin(fold_idx['train'])]
        valid_data = data.loc[data.index.isin(fold_idx['valid'])]
        fold_data = {'train': train_data, 'valid': valid_data}
        return fold_data


class CrossValidation:
    def __init__(self, folder, strategy):
        self.folder = folder
        self.strategy = strategy
        self.folds_result = {}

    def backtest(self, data):
        self.folder.generate_folds_by_index(data.swaps)
        for fold_name in self.folder.fold_names:

            backtest_train = Backtest(copy.deepcopy(self.strategy))
            backtest_valid = Backtest(copy.deepcopy(self.strategy))

            fold_data = self.folder.get_fold(data.swaps, fold_name)

            backtest_train_history = backtest_train.backtest(fold_data['train'])
            backtest_valid_history = backtest_valid.backtest(fold_data['valid'])

            self.folds_result[fold_name] = {'train': backtest_train_history,
                                            'valid': backtest_valid_history}
        return None





