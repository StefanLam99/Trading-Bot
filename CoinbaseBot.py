import cbpro
import json
from Strategy_Base import Strategy
from CoinbaseAPI import CoinbaseAPI
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from time import time, sleep


class CoinbaseBot(object):

    def __init__(self, client):
        self.client = client

    def get_n_orders(self):
        return len(self.client.get_orders())

    def get_balance(self, currency="EUR"):
        balance = -1
        for account in self.client.get_accounts():
            if account["currency"] == currency:
                balance = account["balance"]
        return balance

    def run(self, strategy: Strategy, capital, product_id='BTC-EUR', entried=False, lookback=60 * 2,
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
        api = CoinbaseAPI(client=self.client, symbol=product_id)
        api.get_minute_data(interval_min=1, lookback=lookback)

        # Initialization
        start_time = time()
        entried_time = -1
        unentried_time = -1
        last_buying_price = -1

        if entried:
            buy_order = {"status": "done"}
            sell_order = {"status": None}
        else:
            buy_order = {"status": None}
            sell_order = {"status": "done"}

        columns = ["Buy date", "Buy price", "Sell date", "Sell price", "Start capital", "End capital", "Return", "Size",
                   "Product ID", "Buy ID", "Sell ID"]
        df_trades = pd.DataFrame(columns=columns)

        # check the running time
        while (time() - start_time) / 60 < running_time:

            df = api.update_minute_data()
            #row = df.iloc[-1, :].copy()
            df["last_buying_price"] = last_buying_price
            action = strategy.action(df.copy(), entried=entried)
            current_time = pd.to_datetime(time(), unit="s").strftime("%Y-%m-%d %H:%M")
            print("Time: %s, Entried: %s, Action: %s" % (str(current_time), entried, action))

            # BUYING and SELLING:
            # ------------------------------------------------------------------------------------------------------
            try:
                if not entried:  # try to buy
                    if action == "BUY" and sell_order["status"] == "done":
                        buy_time = pd.to_datetime(time(), unit="s").strftime("%Y-%m-%d %H:%M")
                        buy_price = round(row.Close * 0.97, 2)
                        last_buying_price = buy_price
                        buy_size = round(capital / buy_price, 6)
                        buy_order = self.client.place_limit_order(product_id=product_id, side="buy", price=buy_price,
                                                                  size=buy_size)
                        entried = True
                        entried_time = time()

                        # stats
                        print("Placed BUY order with the following details:")
                        print(buy_order)
                        print("\n")

                    # cancel SELL order when the cancel time is reached
                    if (time() - unentried_time) / 60 > cancel_time and sell_order["status"] != "done" and buy_order[
                        "status"] == "done":
                        print("Canceled SELL order with the following details:")
                        print(sell_order)
                        print("\n")
                        self.client.cancel_order(sell_order["id"])
                        entried = True

                else:  # try to sell
                    if action == "SELL" and buy_order["status"] == "done":
                        sell_time = pd.to_datetime(time(), unit="s").strftime("%Y-%m-%d %H:%M")
                        sell_price = round(row.Open, 2)
                        sell_size = round(buy_order["size"], 6)
                        sell_order = self.client.place_limit_order(product_id=product_id, side="sell", price=sell_price,
                                                                   size=sell_size)
                        unentried_time = time()
                        entried = False
                        capital = sell_price * sell_size * 0.995  # factor 0.995 to ensure we have sufficient funds, since there are fees

                        # stats
                        print("Placed SELL order with the following details:")
                        print(sell_order)
                        print("\n")

                    # cancel BUY order when the cancel time is reached
                    if (time() - entried_time) / 60 > cancel_time and buy_order["status"] != "done" \
                            and sell_order["status"] == "done":
                        print("Canceled BUY order with the following details:")
                        print(buy_order)
                        print("\n")
                        self.client.cancel_order(buy_order["id"])
                        entried = False

                        # we sold if we are not entried here
                        if not entried:
                            if buy_order["status"] == "done" and sell_order["status"] == "done":
                                trade = {"Buy date": buy_time
                                    , "Buy price": buy_price
                                    , "Buy ID": buy_order["ID"]
                                    , "Sell date": sell_time
                                    , "Sell price": sell_price
                                    , "Sell ID": sell_order["ID"]
                                    , "Start capital": buy_size * buy_price
                                    , "End capital": sell_size * sell_price
                                    , "Return": (sell_price - buy_price) / buy_price
                                    , "Size": sell_size
                                    , "Product ID": product_id}
                                df_trade = pd.DataFrame(columns=columns)
                                df_trade = df_trade.append(trade, ignore_index=True)
                                df_trade.to_csv("Trades.csv", mode="a", header=False)
                                df_trades = df_trades.append(trade, ignore_index=True)

                        # -------------------------------------------------------------------------------------------------------------------

                sleep(60)

            except Exception as e:
                print("Time: %s, Entried: %s, Action: %s" % (str(current_time), entried, action))
                print("An error had occured: ")
                print(e)
                sleep(60)

        # out of the while loop so...
        if buy_order["status"] != "done":  # <==> == "open"
            self.client.cancel_order(buy_order["id"])
        if sell_order["status"] != "done":
            self.client.cancel_order(sell_order["id"])
            self.client.place_market_order(product_id, side="sell", size=sell_order['size'])
        print("Reached end of the allowed running time")

        return df_trades


if __name__ == "__main__":
    pass
