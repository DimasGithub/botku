import pandas as pd
import ta
from core.trend_filter import is_uptrend, is_strong_trend

def process_symbol_data(symbol, closes, macd_prev):
    if len(closes) < 50:
        return None

    series = pd.Series(closes)
    macd_line = ta.trend.macd(series)
    signal_line = ta.trend.macd_signal(series)
    rsi = ta.momentum.rsi(series).iloc[-1]

    if macd_line.isna().any() or signal_line.isna().any():
        return None

    macd_now = macd_line.iloc[-1]
    signal_now = signal_line.iloc[-1]

    if macd_prev is not None:
        if macd_prev < signal_now and macd_now > signal_now and is_uptrend(closes) and is_strong_trend(closes):
            return {"message": f"📈 {symbol}: MACD Cross Up + Uptrend", "macd_now": macd_now}
        elif macd_prev > signal_now and macd_now < signal_now:
            return {"message": f"📉 {symbol}: MACD Cross Down → SELL", "macd_now": macd_now}

    return {"macd_now": macd_now}