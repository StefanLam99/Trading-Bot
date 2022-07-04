from Strategy_Base import Strategy


class StrategyHawkie(Strategy):

    def __init__(self, stop_loss=0.98, RSI_buy=40, RSI_sell=70, returns_buy=1.000):
        super().__init__(stop_loss)

    def sell_signal(self, row, entried):
        pass

    def buy_signal(self, row, entried):
        pass