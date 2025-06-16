import requests

resp = requests.get(
    "https://api.mexc.com/api/v3/klines",
    params={"symbol": "BTCUSDT", "interval": "2h", "limit": 50},
)
data = resp.json()
print("data ", data)
closes = [float(candle[4]) for candle in data]