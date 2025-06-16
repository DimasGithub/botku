import pandas as pd
import ta

def is_uptrend(closes, window=50):
    series = pd.Series(closes)
    ema = ta.trend.ema_indicator(series, window=window).ema_indicator()
    return series.iloc[-1] > ema.iloc[-1]

def is_strong_trend(closes, window=14):
    series = pd.Series(closes)
    adx = ta.trend.adx(series, window=window).adx()
    return adx.iloc[-1] > 25
