import cbpro
import json
from Strategy_Base import Strategy
from strategies.Strategy_RSI_SMA_RETURN import Strategy_RSI_SMA_RETURN
from CoinbaseAPI import CoinbaseAPI
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from time import time, sleep
from Utils import convert_time_to_str


class CoinbaseBot(object):

    def __init__(self, client, capital, product_id='BTC-EUR'):
        self.client = client
        self.product_id = product_id
        self.capital = capital
        self.api = CoinbaseAPI(client=self.client, symbol=self.product_id)
        self.df_trades_dict = {"Buy date": [],
                               "Buy price": [],
                               "Buy Size": [],
                               "Buy ID": [],
                               "Sell date": [],
                               "Sell price": [],
                               "Sell ID": [],
                               "Start capital": [],
                               "End capital": [],
                               "Return": [],
                               "Profit": [],
                               "Product ID": []}

    def get_n_orders(self):
        return len(self.client.get_orders())

    def get_balance(self, currency="EUR"):
        balance = -1
        for account in self.client.get_accounts():
            if account["currency"] == currency:
                balance = account["balance"]
        return balance

    def place_buy_order(self, row, price=None, size=None, price_multiplier=0.97, verbose=1):
        price = round(row.Close * price_multiplier, 2) if price is None else price
        size = round(self.capital / price, 6) if size is None else size
        order = self.client.place_limit_order(product_id=self.product_id, side="buy", price=price,
                                              size=size)
        # stats
        if verbose:
            print("Placed BUY order with the following details:")
            print(order)
            print("\n")
        return order

    def place_sell_order(self, row, price=None, size=None, price_multiplier=0.995, verbose=1):
        price = round(row.Close, 2) if price is None else price
        size = -1 if size is None else size  # TODO: fix this
        order = self.client.place_limit_order(product_id=self.product_id, side="sell", price=price,
                                              size=size)

        # stats
        if verbose:
            print("Placed SELL order with the following details:")
            print(order)
            print("\n")
        return order

    def update_buy_order(self, order):
        self.df_trades_dict['Buy date'].append(order['created_at'])
        self.df_trades_dict['Buy price'].append(order['price'])
        self.df_trades_dict['Buy size'].append(order['size'])
        self.df_trades_dict['Buy ID'].append(order['id'])

    def update_sell_order(self, order):
        self.df_trades_dict['Sell date'].append(order['created_at'])
        self.df_trades_dict['Sell price'].append(order['price'])
        self.df_trades_dict['Sell size'].append(order['size'])
        self.df_trades_dict['Sell ID'].append(order['id'])

    def update_final_order(self):
        """
        Update the order trades dict after buying and selling
        """
        self.df_trades_dict['Start capital'].append(self.df_trades_dict['Buy size'] * self.df_trades_dict['Buy price'])
        self.df_trades_dict['End capital'].append(self.df_trades_dict['Sell size'] * self.df_trades_dict['Sell price'])
        self.df_trades_dict['Profit'].append(self.df_trades_dict['Sell size'] - self.df_trades_dict['Buy price'])
        self.df_trades_dict['Return'].append((self.df_trades_dict['Sell size'] - self.df_trades_dict['Buy price'])
                                             / self.df_trades_dict['Buy price'])

    def save_trades(self, path='Trades.csv'):
        df = pd.DataFrame.from_dict(self.df_trades_dict)
        df['Product ID'] = self.product_id
        df.to_csv(path, mode='a')

    def run(self, strategy: Strategy, product_id=None, entried=False, lookback=60 * 2,
            running_time=60 * 2, cancel_time=30):
        """
        Main to run the trading bot

        Parameters
        ----------

        strategy: Strategy
             Object that inherits from Strategy which is able to return
             'BUY', 'SELL', 'NO TRADE' with the 'action' method

        capital: float
            the starting capital to start the trading bot

        product_id: str
            string of the currency you want to trade

        running_time: float
            amount of time you want to run the trading bot given in minutes

        lookback : int
            The number of minutes to lookback starting from the current timestamp

        entried: boolean
            whether we are already entried or not

        cancel_time: float
            time we can wait before we cancel a buy/sell order in minutes

        Returns
        -------

        df_trades: DataFrame
            a DataFrame containing the trades that have taken place in the running time

        """

        # Obtain and initialize the data
        self.api.get_minute_data(interval_min=1, lookback=lookback)

        # Initialization
        start_time = time()
        last_buying_price = -1
        product_id = product_id if product_id is not None else self.product_id
        order = None

        # check the running time
        while (time() - start_time) / 60 < running_time:

            df = self.api.update_minute_data()
            last_row = df.iloc[-1, :].copy()
            df["last_buying_price"] = last_buying_price
            action = strategy.action(df.copy(), entried=entried)
            current_time_str = convert_time_to_str(time())
            print("Time: %s, Entried: %s, Action: %s" % (str(current_time_str), entried, action))

            # BUYING and SELLING:
            # ------------------------------------------------------------------------------------------------------
            try:
                if order is None:  # no order placed yet
                    order_time = time()
                    if not entried and action == "BUY":  # try to buy
                        order = self.place_buy_order(last_row)
                    elif entried and action == "SELL":  # try to sell
                        order = self.place_sell_order(last_row, size=round(prev_order['size'], 6))

                else:  # check whether the order is done
                    order = client.get_order(order_id=order['id'])
                    prev_order = order.copy()  # remember the previous order
                    if order['status'] == 'done':
                        if order['side'] == 'buy':  # we bought
                            entried = True
                            last_buying_price = order['price']
                            self.update_buy_order(order)
                        elif order['side'] == 'sell':  # we sold
                            entried = False
                            self.capital = self.get_balance()
                            self.update_sell_order(order)
                            self.update_final_order()

                        order = None  # reset the order

                    if (time() - order_time) / 60 > cancel_time:
                        print("Canceled BUY order with the following details:")
                        print(order)
                        self.client.cancel_order(order["id"])
                        order = None

            except Exception as e:
                print("An error had occured: ")
                print(e)

            sleep(60)  # ensure we do not send too many requests to the server

        # out of the while loop so...
        self.save_trades()
        if prev_order['side'] == 'buy' and prev_order["status"] != "done":
            self.client.cancel_order(prev_order["id"])

        if prev_order['side'] == 'sell' and prev_order["status"] != "done":
            self.client.cancel_order(prev_order["id"])
            self.client.place_market_order(product_id, side="sell", size=prev_order['size'])

        print("Reached end of the allowed running time")

        return self.df_trades_dict


if __name__ == "__main__":
    config_file = "configs/config_trading_bot.json"

    with open(config_file) as json_data_file:
        config = json.load(json_data_file)
    client = cbpro.AuthenticatedClient(config["api_public"], config["api_secret"], config["passphrase"])

    bot = CoinbaseBot(client=client, product_id='BTC-EUR', capital=100)
    bot.run(strategy=Strategy_RSI_SMA_RETURN(), running_time=720)
