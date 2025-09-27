import json
import threading
import requests
import pandas as pd
from websocket import WebSocketApp
from core.indicator import process_symbol_data
from config.settings import WEBSOCKET_URL, REST_KLINE_URL

symbol_data = {}
ws_app = None
callback_send = None
callback_error = None
KLINE_SYMBOLS = []
last_candle_time = {}

def set_kline_symbols(symbols):
    global KLINE_SYMBOLS
    KLINE_SYMBOLS = symbols

def fetch_initial_klines(symbol, interval="60m", limit=100):
    try:
        url = f"{REST_KLINE_URL}?symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return [float(entry[4]) for entry in data]  # close price
    except Exception as e:
        return []


def get_symbol_data(symbol):
    return symbol_data.get(symbol, {})

def init_symbol_data(symbols):
    global symbol_data, last_candle_time
    symbol_data = {}
    for symbol in symbols:
        closes = fetch_initial_klines(symbol)
        symbol_data[symbol] = {
            "closes": closes,
            "macd_prev": None
        }
        last_candle_time[symbol] = None

def on_message(ws, message):
    try:
        data = json.loads(message)
        if 'd' not in data or 'k' not in data['d']:
            return

        kline = data['d']['k']
        symbol = data.get('s')
        candle_time = kline['t']
        close_price = float(kline['c'])

        if last_candle_time.get(symbol) != candle_time:
            print(f"New close for {symbol}: {close_price} at {candle_time}")
            symbol_data[symbol]["closes"].append(close_price)
            if len(symbol_data[symbol]["closes"]) > 100:
                symbol_data[symbol]["closes"].pop(0)

            last_candle_time[symbol] = candle_time
            result = process_symbol_data(symbol, symbol_data[symbol]["closes"], symbol_data[symbol]["macd_prev"])
            if result:
                print("result ", result)
                symbol_data[symbol]["macd_prev"] = result["macd_now"]
                # if callback_send:
                #     callback_send(result["message"])

    except Exception as e:
        print("Error parsing message:", e)
        if callback_error:
            callback_error(str(e))

def on_open(ws):
    print("WebSocket connected")
    params = [f"spot@public.kline.v3.api@{s}@Min60" for s in KLINE_SYMBOLS]
    print("Subscription topics:", params)
    if not params:
        print("No subscription topics. Check your symbols.")
        return
    payload = {
        "method": "SUBSCRIPTION",
        "params": params,
        "id": 1
    }
    ws.send(json.dumps(payload))

def on_error(ws, error):
    print("WebSocket error:", error)
    if callback_error:
        callback_error(str(error))

def start_websocket(send_callback):
    global ws_app, callback_send
    callback_send = send_callback
    ws_app = WebSocketApp(
        WEBSOCKET_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error
    )
    threading.Thread(target=ws_app.run_forever, daemon=True).start()