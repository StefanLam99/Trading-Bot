import cbpro
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import matplotlib.dates as mdates
from time import sleep, time
import ta
from datetime import datetime, timedelta


def backtest(strategy, df, capital=1000):
    """
    Backtest your strategy with this function

    Parameters
    ----------

    strategy : Strategy object
        Object that has StrategyBase as parent class

    df : pandas dataframe
        dataframe containing the trading data

    capital : float
        capital we can use

    Returns
    -------
    Pandas dataframe
        dataframe containing the buying/selling dates with the profits, returns and open prices


    """

    buying_dates = []
    buying_open_prices = []
    selling_dates = []
    selling_open_prices = []
    capital_list = [capital]
    crypto_list = []  # list of the number of crypto that is bought with the current capital
    entried = False

    # check per row whether we want to buy or sell the stock
    for i in range(len(df) - 1):
        row = df.iloc[i].copy()
        next_row = df.iloc[i + 1].copy()
        if entried:
            row["last_buying_price"] = buying_open_prices[-1]
            df["last_buying_price"] = buying_open_prices[-1]

        action = strategy.action(df.iloc[0:i+1, :].copy(), entried)
        timestamp = next_row.name

        if action == "BUY" and capital > 0 and not entried:
            entried = True
            buying_dates.append(timestamp)
            buying_open_prices.append(next_row.Open)
            crypto_list.append(capital_list[-1] / next_row.Open)
        elif action == "SELL" and entried:
            entried = False
            selling_dates.append(timestamp)
            selling_open_prices.append(next_row.Open)
            capital_list.append(crypto_list[-1] * next_row.Open)

    # if we have more buying dates, then it means that the last selling date has not taken place yet
    if len(buying_dates) > len(selling_dates):
        buying_dates = buying_dates[:-1]
        buying_open_prices = buying_open_prices[:-1]

    actual_trades = pd.DataFrame(
        {"buying_date": buying_dates, "selling_date": selling_dates, "buying_open_price": buying_open_prices,
         "selling_open_price": selling_open_prices})

    # plot results
    plt.style.use("ggplot")
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 12))
    ax1 = axes[0, 0]
    ax2 = axes[1, 0]
    ax3 = axes[0, 1]

    # ax1
    df.plot(kind="line", y="Open", ax=ax1, linewidth=0.7, alpha=0.5)

    df.plot(kind="line", y="SMA60", alpha=0.5, ax=ax1, label="SMA60")
    df.plot(kind="line", y="EMA60", c="purple", alpha=0.5, ax=ax1, label="EMA60")
    actual_trades.plot(kind="scatter", s=20, c="red", x="buying_date", y="buying_open_price", ax=ax1, label="BUY",
                       alpha=1)
    actual_trades.plot(kind="scatter", s=20, c="green", x="selling_date", y="selling_open_price", ax=ax1, label="SELL",
                       alpha=1)
    ax1.set_xlabel("time")
    ax1.set_ylabel("price")
    # ax2
    df.plot(kind="line", y="RSI", linewidth=0.5, alpha=1, ax=ax2, label="RSI")
    ax2.set_ylim((0, 100))
    ax2.axhline(50, c="black")
    ax2.axhline(30, c="black")
    ax2.set_xlabel("time")
    # ax3
    df.plot(kind="line", y="pct change", c="orange", linewidth=0.7, alpha=1, ax=ax3, label="pct change")
    df.plot(kind="line", y="CUM_RETURNS_60", c="green", linewidth=1, alpha=0.7, ax=ax3, label="CUM_RETURNS_60")
    ax3.set_xlabel("time")

    plt.gcf().autofmt_xdate()
    plt.show()

    # if there are actual trades retrieve the performance measures
    if len(actual_trades) > 0:
        # performance measures
        profits = df.loc[actual_trades.selling_date].Open.values - df.loc[actual_trades.buying_date].Open.values
        winning_rate = np.sum([profits > 0]) / len(profits)
        returns = (df.loc[actual_trades.selling_date].Open.values - df.loc[actual_trades.buying_date].Open.values) / \
                  df.loc[actual_trades.buying_date].Open.values

        # adding performance measures to dataframe
        actual_trades["profit"] = profits
        actual_trades["return"] = returns

        # print results
        print("ACTUAL TRADES:")
        print(actual_trades)
        print("\n")
        print("profit: %.2f" % sum(profits))
        print("average returns:  %.6f" % (sum(returns) / max(1, len(returns))))
        print("returns:  %.6f" % (np.prod(returns + 1) - 1))
        print("winning rate:  %.2f" % (winning_rate))
        print("\n")
        print("starting capital: %.2f" % capital)
        print("end capital: %.2f" % capital_list[-1])
        print("return: %.6f" % ((capital_list[-1] - capital) / capital))
        return actual_trades
    else:

        print("NO TRADES HAVE TAKEN PLACE")
        return None
