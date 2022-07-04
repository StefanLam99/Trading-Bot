import json
import time

from Backtesting import backtest
from Strategy_RSI_SMA_RETURN import Strategy_RSI_SMA_RETURN
from Strategy_LSTM import Strategy_LSTM
import cbpro
import pandas as pd
from datetime import datetime, timedelta
from CoinbaseAPI import CoinbaseAPI

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
config_file = "configs/config_trading_bot.json"


with open(config_file) as json_data_file:
    config = json.load(json_data_file)
client = cbpro.AuthenticatedClient(config["api_public"], config["api_secret"], config["passphrase"])
api = CoinbaseAPI(client=client, symbol='BTC-EUR')
df = api.get_minute_data(interval_min=60, lookback=24*60*30*3)
strat = Strategy_RSI_SMA_RETURN()

first_training_date = '2021-12-01'
last_training_date = '2022-02-01'
strat_lstm = Strategy_LSTM(first_training_date=first_training_date, last_training_date=last_training_date, data=df)
results = backtest(strat_lstm, df=df)
print(df)
