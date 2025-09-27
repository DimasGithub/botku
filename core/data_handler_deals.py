import json
import threading
import pandas as pd
from websocket import WebSocketApp, create_connection
from core.indicator import process_symbol_data
from config.settings import WEBSOCKET_URL

symbol_data = {}
ws_app = None
callback_send = None

DEAL_SYMBOLS = []
KLINE_SYMBOLS = []

def get_symbol_data(symbol):
    return symbol_data.get(symbol, {})

def init_symbol_data(symbols):
    global symbol_data
    symbol_data = {
        symbol: {
            "closes": [],
            "macd_prev": None
        } for symbol in symbols
    }

def on_message(ws, message):
    try:
        data = json.loads(message)
        if 'd' in data and 'deals' in data['d']:
            symbol = data.get('s')
            price = float(data['d']['deals'][0]['p'])
        elif 'd' in data and 'c' in data['d']:
            symbol = data.get('s')
            price = float(data['d']['c'])
        else:
            return

        closes = symbol_data[symbol]["closes"]
        closes.append(price)

        if len(closes) > 100:
            closes.pop(0)

        result = process_symbol_data(symbol, closes, symbol_data[symbol]["macd_prev"])

        if result:
            symbol_data[symbol]["macd_prev"] = result["macd_now"]
            if "message" in result and callback_send:
                callback_send(result["message"])

    except Exception as e:
        print("Error parsing message:", e)

def on_open(ws):
    global DEAL_SYMBOLS
    params = []
    for s in DEAL_SYMBOLS:
        params.append(f"spot@public.deals.v3.api@{s}")
    for s in KLINE_SYMBOLS:
        params.append(f"spot@public.kline.v3.api@{s}@Min1")

    payload = {
        "method": "SUBSCRIPTION",
        "params": params,
        "id": 1
    }
    ws.send(json.dumps(payload))

def update_symbol_lists(new_symbols):
    global DEAL_SYMBOLS, KLINE_SYMBOLS
    DEAL_SYMBOLS = []
    KLINE_SYMBOLS = []

    for symbol in new_symbols:
        mode = detect_symbol_mode(symbol)
        if mode == "deal":
            DEAL_SYMBOLS.append(symbol.upper())
        else:
            KLINE_SYMBOLS.append(symbol.upper())

    print("DEAL_SYMBOLS:", DEAL_SYMBOLS)
    print("KLINE_SYMBOLS:", KLINE_SYMBOLS)


def on_error(ws, error):
    from telegram_bot.bot import send_telegram_error_message 

    print("WebSocket error:", error)
    send_telegram_error_message(f"WebSocket Error:\n{error}")

def on_close(ws, close_status_code, close_msg):
    from telegram_bot.bot import send_telegram_error_message 

    print("WebSocket closed")
    send_telegram_error_message("WebSocket connection closed unexpectedly!")

def detect_symbol_mode(symbol: str) -> str:
    try:
        ws = create_connection("wss://wbs.mexc.com/ws")
        payload = {
            "method": "SUBSCRIPTION",
            "params": [f"spot@public.deals.v3.api@{symbol}"],
            "id": 999
        }
        ws.send(json.dumps(payload))
        ws.settimeout(3)
        result = ws.recv()
        ws.close()

        if "deals" in result:
            return "deal"
    except Exception as e:
        print(f"Fallback to kline for {symbol} → {e}")
    
    return "kline"

def start_websocket(send_callback):
    global ws_app, callback_send
    callback_send = send_callback
    ws_app = WebSocketApp(
        WEBSOCKET_URL,
        on_open=on_open,
        on_message=on_message
    )
    threading.Thread(target=ws_app.run_forever, daemon=True).start()
