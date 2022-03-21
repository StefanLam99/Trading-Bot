import pandas as pd
import numpy as np

from ta.momentum import rsi
from ta.trend import sma_indicator, ema_indicator
from datetime import datetime, timedelta


class CoinbaseAPI:
    """
    API to retrieve trade data from Coinbase
    """

    def __init__(self, client):
        self.client = client
        self.df = pd.DataFrame()

    def update_minute_data(self, symbol, interval_min=1, lookback=1):
        self.df = self.get_minute_data(symbol=symbol, interval_min=interval_min, lookback=lookback)
        return self.df

    def get_minute_data(self, symbol, interval_min=1, lookback=24 * 60, max_requests=300):
        """
        Method to obtain minute data from the Coinbase Pro API

        Parameters
        ----------

        symbol : str
             Symbol of the currency, e.g., "BTC-EUR", "DOT-EUR", "BTC-USD", "DOT-USD"

        interval_min : int
                The interval in minutes between the retrieved timestamps, can only be in the following range [1, 5, 15, 60, 360, 1440]

        lookback : int
            The number of minutes to lookback starting from the current timestamp

        max_requests : int
            The max number of timestamps you can request per time

        Returns
        -------
        Pandas Dataframe
            a dataframe with the trade data


        """

        interval_sec = interval_min * 60  # interval in seconds
        end = pd.to_datetime(self.client.get_time()["epoch"], unit="s")  # end date
        start = end - timedelta(minutes=lookback)  # start date
        delta = timedelta(minutes=min(lookback, max_requests) * interval_min)  # time between each timestamp
        n_timestamps = int(lookback / interval_min)
        current_start = start
        current_end = -1
        try:
            # one request can only retrieve up to max_requests timestamps: use for loop to obtain the desired range with
            # multiple requests
            dataframes = [self.df]
            for i in range(int(n_timestamps / max_requests)):
                current_end = current_start + delta
                dataframes.append(pd.DataFrame(
                    self.client.get_product_historic_rates(symbol, current_start.isoformat(), current_end.isoformat(),
                                                           interval_sec))[::-1])
                current_start = current_end
            dataframes.append(pd.DataFrame(
                self.client.get_product_historic_rates(symbol, current_start.isoformat(), end, interval_sec))[::-1])
            self.df = pd.concat(dataframes)
        except RuntimeError:
            print("ERROR:")
            print(self.client.get_product_historic_rates(symbol, current_start.isoformat(), current_end.isoformat(),
                                                         interval_sec))  # should print what error we got

        # clean dataframe
        self.df.columns = ["Time", "Low", "High", "Open", "Close", "Volume"]
        self.df = self.df.astype(float)
        self.df = self.df.set_index("Time")
        self.df.index = pd.to_datetime(self.df.index, unit="s")

        # add some measures
        self.df['RSI'] = rsi(self.df.Close, window=10)
        self.df['SMA200'] = sma_indicator(self.df.Close, window=200)
        self.df['EMA200'] = ema_indicator(self.df.Close, window=200)
        self.df['SMA100'] = sma_indicator(self.df.Close, window=100)
        self.df['EMA100'] = ema_indicator(self.df.Close, window=100)
        self.df['SMA50'] = sma_indicator(self.df.Close, window=50)
        self.df['EMA50'] = ema_indicator(self.df.Close, window=50)
        self.df['SMA60'] = sma_indicator(self.df.Close, window=60)
        self.df['EMA60'] = ema_indicator(self.df.Close, window=60)

        self.df["pct change"] = self.df.Open.pct_change() + 1
        self.df["CUM_RETURNS_50"] = (self.df.Open.pct_change() + 1).rolling(50).apply(np.prod)
        self.df["CUM_RETURNS_60"] = (self.df.Open.pct_change() + 1).rolling(60).apply(np.prod)
        self.df["CUM_RETURNS_100"] = (self.df.Open.pct_change() + 1).rolling(100).apply(np.prod)

        return self.df



