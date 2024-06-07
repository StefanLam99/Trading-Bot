import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from Utils import check_save_location
from fpdf import FPDF


def backtest(strategy, df, capital=1000, symbol=''):
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

    symbol : str
        symbol of the currency

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

        action = strategy.action(df.iloc[0:i + 1, :].copy(), entried)
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
    time_slots = df.index.strftime('%d-%m-%Y')
    save_path_plots = f'results_backtesting/{strategy.__module__}/{symbol}/plots/{time_slots[0]}_to_{time_slots[-1]}.png'
    plot_results(df=df, actual_trades=actual_trades, save_path=save_path_plots)

    # if there are actual trades retrieve the performance measures
    if len(actual_trades) > 0:
        # performance measures
        wins = (df.loc[actual_trades.selling_date].Open.values - df.loc[actual_trades.buying_date].Open.values) > 0
        winning_rate = np.sum([wins]) / len(wins)
        returns = (df.loc[actual_trades.selling_date].Open.values - df.loc[actual_trades.buying_date].Open.values) / \
                  df.loc[actual_trades.buying_date].Open.values

        # adding performance measures to dataframe
        actual_trades["return"] = returns
        texts = [f"average returns: {(sum(returns) / max(1, len(returns))):.6f}\n",
                 f"returns: {(np.prod(returns + 1) - 1):.6f}",
                 f"winning rate:  {winning_rate:.2f}",
                 f"starting capital: {capital:.2f}",
                 f"end capital: {capital_list[-1]:.2f}",
                 f"return: {(capital_list[-1] - capital) / capital:.6f}"]
        print('\n'.join(texts))
    else:
        texts = ["NO TRADES HAVE TAKEN PLACE"]
        print("NO TRADES HAVE TAKEN PLACE")

    # make pdf
    save_path_pdf = f'results_backtesting/{strategy.__module__}/{symbol}/pdfs/{time_slots[0]}_to_{time_slots[-1]}.pdf'
    make_pdf(actual_trades=actual_trades, texts=texts, symbol=symbol, save_path_pdf=save_path_pdf, save_path_plots=save_path_plots)

    return actual_trades


def make_pdf(actual_trades: pd.DataFrame = None, texts: str = None, symbol: str = "", save_path_pdf: str = None,
             save_path_plots: str = None):
    pdf = FPDF(orientation='L')
    pdf.set_font("Arial", style='B', size=20)
    pdf.add_page()
    pdf.cell(200, 10, txt=f"Results for {symbol}", align='C', ln=1)
    pdf.set_font("Arial", size=15)
    for text in texts:
        pdf.cell(200, 10, txt=text, ln=1)

    # plot actual trades
    if len(actual_trades) > 0 and actual_trades is not None:
        pdf.set_font("Arial", size=8)
        actual_trades = actual_trades.round(2)
        pdf.add_page()
        for col in list(actual_trades.columns):
            pdf.cell(40, 13, txt=col, border=1)
        pdf.ln()
        for i, row in actual_trades.iterrows():
            for val in row:
                pdf.cell(40, 13, txt=str(val), border=1)
            pdf.ln()
    pdf.add_page()
    pdf.image(save_path_plots, 0, 0, 300, 200)
    check_save_location(save_path_pdf)
    pdf.output(save_path_pdf)


def plot_results(df: pd.DataFrame, actual_trades: pd.DataFrame, save_path: str = None):
    # plot results
    plt.style.use("ggplot")
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 12))
    ax1 = axes[0, 0]
    ax2 = axes[1, 0]
    ax3 = axes[0, 1]

    # ax1
    df.plot(kind="line", y="Close", ax=ax1, linewidth=0.7, alpha=0.5)

    df.plot(kind="line", y="SMA60", alpha=0.5, ax=ax1, label="SMA60")
    df.plot(kind="line", y="EMA60", c="purple", alpha=0.5, ax=ax1, label="EMA60")
    df.plot(kind="line", y="SMA60", alpha=0.5, ax=ax1, label="SMA200")
    df.plot(kind="line", y="EMA60", alpha=0.5, ax=ax1, label="EMA200")
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
    check_save_location(save_path)
    plt.savefig(save_path)
