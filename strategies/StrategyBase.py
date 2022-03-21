import cbpro
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from time import sleep, time
import ta
from ta.momentum import rsi
from ta.trend import sma_indicator, ema_indicator
from datetime import datetime, timedelta


class Strategy(object):
    """
    Base class for strategies
    """

    def __init__(self, row, entried, stop_loss):
        self.row = row
        self.entried = entried
        self.stop_loss = stop_loss

    def buy_signal(self):
        raise NotImplementedError

    def sell_signal(self):
        raise NotImplementedError

    def action(self):
        buy_signal = self.buy_signal()  # RSI SMA strategy
        sell_signal = self.sell_signal()

        # not entried yet so try to buy
        if not self.entried and buy_signal:
            return "BUY"  # buy next open

        # entried into a buy position so try to sell at a good price
        if self.entried and sell_signal:
            price_change_since_buying = self.row.Open / self.row.last_buying_price
            if sell_signal:
                return "SELL"  # sell next open
            elif price_change_since_buying < self.stop_loss:
                print("stop loss")
                return "SELL"

        return "NO TRADE"  # No trade has happened




