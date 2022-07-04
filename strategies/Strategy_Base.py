import pandas as pd


class Strategy(object):
    """
    Base class for strategies
    """

    def __init__(self, stop_loss=0.95):
        self.stop_loss = stop_loss

    def buy_signal(self, df, entried):
        raise NotImplementedError

    def sell_signal(self, df, entried):
        raise NotImplementedError

    def action(self, df, entried=False):
        """
        Determines the action based on the buy and sell signals

        Parameters
        ----------

        df : pd.DataFrame
            DataFrame with the latest data

        entried : boolean
            Whether we are already entried

        Returns
        -------
        str
            A string with the action: "BUY", "SELL" or "NO TRADE"
        """

        row = df.iloc[-1, :]
        buy_signal = self.buy_signal(df, entried)  # RSI SMA strategy
        sell_signal = self.sell_signal(df, entried)

        # not entried, so try to buy (closed position)
        if not entried and buy_signal:
            return "BUY"  # buy next open

        # entried, so try to sell at a good price (open position)
        if entried:
            price_change_since_buying = row.Close / row.last_buying_price
            if sell_signal:
                return "SELL"  # sell next open
            elif price_change_since_buying < self.stop_loss:
                return "SELL"

        return "NO TRADE"  # No trade has happened


