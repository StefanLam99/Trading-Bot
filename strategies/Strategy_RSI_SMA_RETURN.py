from Strategy_Base import Strategy


class Strategy_RSI_SMA_RETURN(Strategy):
    """
    Simple strategy based on RSI, SMA and cumulative returns.
    """

    def __init__(self, stop_loss=0.95, RSI_buy=40, RSI_sell=70, returns_buy=1.000):
        """
        Initialization of this simple strategy.

        Parameters
        ----------

        stop_loss : float
            Sell if the returns are < stop_loss [0,1]

        RSI_buy : float
            Buy if RSI < RSI_buy [0,100]

        RSI_sell : float
            Sell if RSI > RSI_sell [0,100]

        returns_buy : float
            Buy if cumulative returns > returns_buy
        """
        super().__init__(stop_loss=stop_loss)
        self.RSI_buy = RSI_buy
        self.RSI_sell = RSI_sell
        self.returns_buy = returns_buy

    def buy_signal(self, df, entried):
        row = df.iloc[-1, :]
        return (row.Close > row.SMA60) & \
               (row.RSI < self.RSI_buy) & \
               (row.CUM_RETURNS_60 > self.returns_buy)

    def sell_signal(self, df, entried):
        row = df.iloc[-1, :]
        return row.RSI > self.RSI_sell
