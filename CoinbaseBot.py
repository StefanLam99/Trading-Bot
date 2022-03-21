import cbpro
import json
from Data import get_minute_data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from time import sleep, time
import ta
from ta.momentum import rsi
from ta.trend import sma_indicator, ema_indicator
from datetime import datetime, timedelta


class CoinbaseBot(object):

    def __init__(self, config_file="config_trading_bot.json"):
        with open(config_file) as json_data_file:
            config = json.load(json_data_file)
        self.client = cbpro.AuthenticatedClient(config["api_public"], config["api_secret"], config["passphrase"])

    def get_n_orders(self):
        return len(self.client.get_orders())

    def get_balance(self, currency="EUR"):
        balance = -1
        for account in self.client.get_accounts():
            if account["currency"] == currency:
                balance = account["balance"]
        return balance



    def run(self):
        pass


if __name__ == "__main__":



