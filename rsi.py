import backtrader as bt


class RSIRollercoasterStrategy(bt.Strategy):

    params = {
        "rsi_period": 11,
        "rsi_low": 40,
        "rsi_high": 56,
        "rsi_mid": 71,
        "sma_period": 130,
        "atr_period": 17,
        "profit_target": 0.02,  # 2% profit target
        "stop_loss": 0.02,  # 2% stop loss
        "sizer": "FixedLotSizer",  # TODO(0): Add link for this sizer docs
        "sizer_lots": 0.03, 
    }

    def __init__(self):
        self.close_price = self.datas[0].close
        self.order = None
        self.rsi = bt.indicators.RelativeStrengthIndex(self.datas[0], period=self.params.rsi_period)
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.sma_period)
        self.atr = bt.indicators.AverageTrueRange(self.datas[0], period=self.params.atr_period)

        self.entry_price = None
        self.lastlen = -1

    def next(self) -> None:
        if (
            hasattr(self.data, "isdelayed") and self.data.isdelayed()
        ):  # prevents from live trading on delayed data
            return
        if self.lastlen == len(self.data):
            return
        self.lastlen = len(self.data)
        if self.order:  # check if there's any open order
            return

        if not self.position:  # not in the market
            if self.rsi[0] < self.p.rsi_low and self.close_price[0] > self.sma[0]:
                self.log(f"Creating BUY order @ {self.close_price[0]}")
                self.entry_price = self.close_price[0]
                self.order = self.buy()
            elif self.rsi[0] > self.p.rsi_high and self.close_price[0] < self.sma[0]:
                pass
        else:  # in the market
            if self.position.size > 0:  # long position
                if (
                    self.rsi[0] > self.p.rsi_mid
                    or self.close_price[0] >= self.entry_price * (1 + self.params.profit_target)
                    or self.close_price[0] <= self.entry_price * (1 - self.params.stop_loss)
                ):
                    self.log(f"Closing LONG position @ {self.close_price[0]}")
                    self.order = self.sell()
            elif self.position.size < 0:  # short position
                if (
                    self.rsi[0] < self.p.rsi_mid
                    or self.close_price[0] <= self.entry_price * (1 - self.params.profit_target)
                    or self.close_price[0] >= self.entry_price * (1 + self.params.stop_loss)
                ):
                    self.log(f"Closing SHORT position @ {self.close_price[0]}")
                    self.order = self.buy()

    def notify_order(self, order: bt.Order) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [
            order.Completed,
            order.Canceled,
            order.Margin,
            order.Rejected,
        ]:
            self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}")

    # Define a helper function to include date/time in logs
    def log(self, txt: str) -> None:
        dt = self.data.datetime.date(0)
        t = self.data.datetime.time(0)
        print(f"{dt} {t} {txt}")
