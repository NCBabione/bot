# EURUSD(5min) best para: {'rsi_period': 17, 'rsi_low': 48, 'rsi_high': 70, 'rsi_mid': 28, 'sma_period': 100, 'atr_period': 13, 'profit_target': 0.01, 'stop_loss': 0.04}
# BTCUSD(5min) best para: {'rsi_period': 18, 'rsi_low': 49, 'rsi_high': 50, 'rsi_mid': 75, 'sma_period': 50, 'atr_period': 9, 'profit_target': 0.01, 'stop_loss': 0.01}
# APPL(5min) best para: {'rsi_period': 11, 'rsi_low': 48, 'rsi_high': 59, 'rsi_mid': 34, 'sma_period': 230, 'atr_period': 14, 'profit_target': 0.01, 'stop_loss': 0.01}
# EURUSD(15min) best para: {'rsi_period': 10, 'rsi_low': 36, 'rsi_high': 60, 'rsi_mid': 63, 'sma_period': 160, 'atr_period': 9, 'profit_target': 0.03, 'stop_loss': 0.04}
# [*] BTCUSD(15min) best para: {'rsi_period': 11, 'rsi_low': 40, 'rsi_high': 56, 'rsi_mid': 71, 'sma_period': 130, 'atr_period': 17, 'profit_target': 0.02, 'stop_loss': 0.02}
# APPL(15min) best para: {'rsi_period': 15, 'rsi_low': 41, 'rsi_high': 52, 'rsi_mid': 70, 'sma_period': 230, 'atr_period': 9, 'profit_target': 0.03, 'stop_loss': 0.03}
# EURUSD(4h) best para: {'rsi_period': 13, 'rsi_low': 43, 'rsi_high': 69, 'rsi_mid': 39, 'sma_period': 230, 'atr_period': 19, 'profit_target': 0.02, 'stop_loss': 0.04}
# BTCUSD(4h) best para: {'rsi_period': 11, 'rsi_low': 33, 'rsi_high': 70, 'rsi_mid': 72, 'sma_period': 90, 'atr_period': 15, 'profit_target': 0.04, 'stop_loss': 0.02}
# AAPL(4h) best para: {'rsi_period': 16, 'rsi_low': 43, 'rsi_high': 84, 'rsi_mid': 70, 'sma_period': 70, 'atr_period': 9, 'profit_target': 0.04, 'stop_loss': 0.03}
import backtrader as bt


class RSIRollercoasterStrategy(bt.Strategy):
    """
    Trading Ruleset:

    Indicators:

        RSI Calculation:

            Use a 14-period RSI to determine overbought and
            oversold conditions.

        Simple Moving Average (SMA):

            Use a 200-period Simple Moving Average to ensure we
            trade in the direction of the long-term trend.

        Average True Range (ATR):

            Use a 14-period ATR to gauge market volatility.

    Entry Rules:

        Buy (Long Position):

            Enter a long position when the RSI crosses
            above 30 (indicating oversold conditions).
            Ensure the closing price is above the 200-period SMA
            to confirm an overall uptrend.

        Sell (Short Position):

            Enter a short position when RSI crosses
            below 70 (indicating overbought conditions).
            Ensure the closing price is below the 200-period SMA
            to confirm an overall downtrend.

    Exit Rules:

        Long Position Exit:

            Exit the position when RSI crosses below 50 (indicating
            a reversion towards neutral territory).
            Alternatively, exit the position if the profit target (e.g., 1% gain)
            or stop loss (e.g., 1% loss) is met.

        Short Position Exit:

            Exit the position when RSI crosses above 50 (indicating
            a reversion towards neutral territory).
            Alternatively, exit the position if the profit target (e.g., 1% gain)
            or stop loss (e.g., 1% loss) is met.

    Additional Filters:

        Intratrade Checks:

            Volatility Check: Ensure that during the trade, the
            current market's ATR value does not exceed a certain
            threshold to avoid high volatility conditions.

            Time of Day Filter:

            Restrict trading to specific times of the day,
            avoiding low liquidity periods (e.g., avoid trading
            during lunch hours or major news announcements).
    """

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
        "sizer_lots": 0.10, # 0.03 $220 dd for gold, 0.05 $378 dd, 0.1 $757 dd, 0.25 $1894 dd, 0.5 $3789 dd, 1.0 $7578 dd, 2.0 $11230 dd
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
