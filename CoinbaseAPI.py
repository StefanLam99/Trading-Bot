import pandas as pd
import numpy as np
import warnings
from ta.momentum import rsi
from ta.trend import sma_indicator, ema_indicator
from datetime import datetime, timedelta


class CoinbaseAPI:
    """
    API to retrieve trade data from Coinbase
    """

    def __init__(self, client, symbol):
        self.client = client
        self.symbol = symbol
        self.cbpro_cols = ["Low", "High", "Open", "Close", "Volume"]
        self.df = pd.DataFrame(columns=self.cbpro_cols)

    def get_minute_data(self, interval_min=1, lookback=24 * 60, max_requests=300):
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
        new_df = pd.DataFrame()
        try:
            # one request can only retrieve up to max_requests timestamps: use for loop to obtain the desired range with
            # multiple requests
            dataframes = []
            for i in range(int(n_timestamps / max_requests)):
                current_end = current_start + delta
                dataframes.append(pd.DataFrame(
                    self.client.get_product_historic_rates(self.symbol, current_start.isoformat(), current_end.isoformat(),
                                                           interval_sec))[::-1])
                current_start = current_end
            dataframes.append(pd.DataFrame(
                self.client.get_product_historic_rates(self.symbol, current_start.isoformat(), end, interval_sec))[::-1])
            new_df = pd.concat(dataframes)
        except RuntimeError:
            print("ERROR:")
            print(self.client.get_product_historic_rates(self.symbol, current_start.isoformat(), current_end.isoformat(),
                                                         interval_sec))  # should print what error we got
        # check whether the new dataframe is empty or not
        if len(new_df) == 0:
            return self.df.copy()

        # clean dataframe
        new_df.columns = ["Time", "Low", "High", "Open", "Close", "Volume"]
        new_df = new_df.astype(float)
        new_df = new_df.set_index("Time")
        new_df.index = pd.to_datetime(new_df.index, unit="s")
        new_df.index = new_df.index + timedelta(hours=1)  # time in netherlands
        new_df = pd.concat([self.df[self.cbpro_cols], new_df])

        # add some measures
        new_df['RSI'] = rsi(new_df.Close, window=10)
        new_df['SMA200'] = sma_indicator(new_df.Close, window=200)
        new_df['EMA200'] = ema_indicator(new_df.Close, window=200)
        new_df['SMA100'] = sma_indicator(new_df.Close, window=100)
        new_df['EMA100'] = ema_indicator(new_df.Close, window=100)
        new_df['SMA50'] = sma_indicator(new_df.Close, window=50)
        new_df['EMA50'] = ema_indicator(new_df.Close, window=50)
        new_df['SMA60'] = sma_indicator(new_df.Close, window=60)
        new_df['EMA60'] = ema_indicator(new_df.Close, window=60)

        new_df["pct change"] = new_df.Close.pct_change() + 1
        new_df["CUM_RETURNS_50"] = (new_df.Close.pct_change() + 1).rolling(50).apply(np.prod)
        new_df["CUM_RETURNS_60"] = (new_df.Close.pct_change() + 1).rolling(60).apply(np.prod)
        new_df["CUM_RETURNS_100"] = (new_df.Close.pct_change() + 1).rolling(100).apply(np.prod)

        self.df = pd.concat([self.df, new_df])
        return self.df.copy()

    def update_minute_data(self):
        """
        Method to update the minute data from the Coinbase Pro API
        """

        current_time = datetime.now()
        time_diff = current_time - self.df.index[-1]
        time_diff_mins = int(time_diff.seconds / 60)
        if time_diff_mins <= 0:  # now new update required
            return self.df.copy()
        else:
            self.df = self.get_minute_data(interval_min=1, lookback=time_diff_mins)
            return self.df.copy()


