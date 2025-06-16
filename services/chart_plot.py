import io
import pandas as pd
import matplotlib.pyplot as plt
import ta

def generate_macd_chart(closes, symbol):
    series = pd.Series(closes)
    macd = ta.trend.macd(series)
    signal = ta.trend.macd_signal(series)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(macd, label="MACD")
    ax.plot(signal, label="Signal")
    ax.set_title(f"{symbol} - MACD Chart")
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf
