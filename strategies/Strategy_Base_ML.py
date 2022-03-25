import numpy as np
import pandas as pd

from Strategy_Base import Strategy
from Utils import obtain_period_data


class Strategy_ML(Strategy):

    def __init__(self, first_training_date, last_training_date, data: pd.DataFrame, epochs=10, lr=0.001, stop_loss=0.95):
        super().__init__(stop_loss=stop_loss)
        self.first_training_date = first_training_date
        self.last_training_date = last_training_date
        self.epochs = epochs
        self.data = data
        self.lr = lr

    def data_processing(self):
        data = self.data.copy()
        data[['Close[-1]', 'SMA50[-1]', 'SMA200[-1]', 'Volume[-1]']] = \
            data[['Close', 'SMA50', 'SMA200', 'Volume']].shift(-1)
        data.shift()
        data = data[['Close', 'Close[-1]', 'SMA50[-1]', 'SMA200[-1]', 'Volume[-1]']]
        data.dropna(inplace=True)

        train_data = data[self.first_training_date:self.last_training_date].copy()
        X_train = train_data[['Close[-1]', 'SMA50[-1]', 'SMA200[-1]', 'Volume[-1]']]
        Y_train = train_data['Close']

        test_data = data[self.last_training_date:].copy()
        X_test = test_data[['Close[-1]', 'SMA50[-1]', 'SMA200[-1]', 'Volume[-1]']]
        Y_test = test_data['Close']

        return np.asarray(X_train), np.asarray(Y_train), np.asarray(X_test), np.asarray(Y_test)

    def fit(self):
        raise NotImplementedError

    def buy_signal(self, row, entried):
        raise NotImplementedError

    def sell_signal(self, row, entried):
        raise NotImplementedError
