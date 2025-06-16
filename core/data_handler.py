
import json
import threading
import pandas as pd
from websocket import WebSocketApp
from core.indicator import process_symbol_data
from config.settings import WEBSOCKET_URL

symbol_data = {}
ws_app = None
callback_send = None
callback_error = None

KLINE_SYMBOLS = []

def init_symbol_data(symbols):
    global symbol_data
    symbol_data = {
        symbol: {
            "closes": [],
            "macd_prev": None,
            "last_candle_time": None 
        } for symbol in symbols
    }
    print("🧠 Initialized symbol_data:", symbol_data)  # DEBUG

def on_message(ws, message):
    try:
        data = json.loads(message)

        if 'd' in data and 'k' in data['d']:
            symbol = data.get('s')
            kline = data['d']['k']
            candle_close_time = kline['t']  # or 'T'
            close_price = float(kline['c'])

            if symbol_data[symbol]["last_candle_time"] != candle_close_time:
                symbol_data[symbol]["last_candle_time"] = candle_close_time
                closes = symbol_data[symbol]["closes"]
                closes.append(close_price)
                if len(closes) > 100:
                    closes.pop(0)

                print(f"✅ {symbol} New candle closed: {close_price} at {candle_close_time}")

                result = process_symbol_data(symbol, closes, symbol_data[symbol]["macd_prev"])
                if result:
                    symbol_data[symbol]["macd_prev"] = result["macd_now"]
                    if callback_send:
                        callback_send(result["message"])
            else:
                print(f"🔄 {symbol} Updating current candle: {close_price}")

    except Exception as e:
        print("❌ Error parsing message:", e)

def on_error(ws, error):
    print("❗ WebSocket error:", error)
    if callback_error:
        callback_error(f"WebSocket Error:\n{error}")

def on_close(ws, close_status_code, close_msg):
    print("🚪 WebSocket closed")
    if callback_error:
        callback_error("WebSocket connection closed unexpectedly!")

def on_open(ws):
    print("🔌 WebSocket connected")
    params = [f"spot@public.kline.v3.api@{s}@Min60" for s in KLINE_SYMBOLS]
    print("🧩 Subscription topics:", params)  # DEBUG topics

    payload = {
        "method": "SUBSCRIPTION",
        "params": params,
        "id": 1
    }
    ws.send(json.dumps(payload))

def set_kline_symbols(new_symbols):
    global KLINE_SYMBOLS
    KLINE_SYMBOLS = []

    for symbol in new_symbols:
        KLINE_SYMBOLS.append(symbol.upper())

    KLINE_SYMBOLS = [s.upper() for s in new_symbols]
    print("✅ KLINE_SYMBOLS set to:", KLINE_SYMBOLS)  # DEBUG

def start_websocket(send_callback):
    global ws_app, callback_send
    callback_send = send_callback
    ws_app = WebSocketApp(
        WEBSOCKET_URL,
        on_open=on_open,
        on_message=on_message
    )
    threading.Thread(target=ws_app.run_forever, daemon=True).start()