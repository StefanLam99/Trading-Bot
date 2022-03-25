import numpy as np
import pandas as pd
import os
from Utils import classify

import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM, BatchNormalization
from keras.losses import MeanSquaredError
from sklearn.model_selection import train_test_split

from Strategy_Base_ML import Strategy_ML


class Strategy_LSTM(Strategy_ML):

    def __init__(self, first_training_date, last_training_date, data: pd.DataFrame, batch_size=100, epochs=10, lr=0.001):
        super().__init__(first_training_date=first_training_date, last_training_date=last_training_date, data=data,
                         epochs=epochs, lr=lr)
        self.batch_size = batch_size
        self.model_path = 'models/LSTM_' + str(self.first_training_date) + '__' + str(self.last_training_date)

        if os.path.exists(self.model_path):
            self.model = keras.models.load_model(self.model_path)
        else:
            # define the model
            self.model = Sequential()
            self.model.add(LSTM(128, input_shape=(1, 4), return_sequences=True))  #TODO: un-hardcode 4
            self.model.add(Dropout(0.2))
            #self.model.add(BatchNormalization())

            self.model.add(LSTM(128, activation='relu', return_sequences=True))
            self.model.add(Dropout(0.1))
            #self.model.add(BatchNormalization())

            self.model.add(LSTM(128, activation='relu'))
            self.model.add(Dropout(0.1))
            #self.model.add(BatchNormalization())

            self.model.add(Dense(32, activation='relu'))
            self.model.add(Dropout(0.2))

            self.model.add(Dense(1, activation='relu'))

            self.fit()

    def fit(self):
        X_train, Y_train, X_test, Y_test = self.data_processing()
        X_train = X_train.reshape(-1, 1, X_train.shape[1])
        Y_train = Y_train.reshape(-1, 1, 1)
        X_test = X_test.reshape(-1, 1, X_test.shape[1])
        Y_test = Y_test.reshape(-1, 1, 1)

        opt = keras.optimizers.Adam(learning_rate=self.lr, decay=1e-6)
        self.model.compile(
            #loss='sparse_categorical_crossentropy',
            loss=MeanSquaredError(),
            optimizer=opt,
            metrics=['accuracy']
        )

        # Train model
        self.model.fit(
            X_train, Y_train,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_data=(X_test,Y_test),
            verbose=1
        )

        self.model.save('models/LSTM_' + str(self.first_training_date) + '__' + str(self.last_training_date))

    def buy_signal(self, df, entried):
        row = df[['Close', 'SMA50', 'SMA200', 'Volume']].iloc[-1, :].copy()
        x = np.asarray(row)
        x = x.reshape(-1, 1, 4)
        y_pred = self.model.predict(x)
        pred = classify(row.Close, y_pred)

        if pred == 1:
            return True
        else:
            return False

    def sell_signal(self, df, entried):
        row = df.iloc[-1, :]
        return row.RSI > 70


