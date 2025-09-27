
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config.settings import TELEGRAM_TOKEN
from core.data_handler import start_websocket, init_symbol_data, symbol_data, set_kline_symbols, ws_app, get_symbol_data
from services.chatgpt import generate_trend_summary
from services.chart_plot import generate_macd_chart

active_chats = set()
current_symbols = ["BTCUSDT"]

bot = Bot(token=TELEGRAM_TOKEN)



def restart_websocket():
    global ws_app
    try:
        if ws_app:
            ws_app.close()
        start_websocket(send_telegram_message)  # kamu bisa sesuaikan callback-nya
    except Exception as e:
        print(f"Failed to restart WebSocket: {e}")


def send_telegram_message(message):
    for chat_id in active_chats:
        try:
            bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print("Telegram Send Error:", e)

def send_telegram_error_message(message):
    for chat_id in active_chats:
        try:
            bot.send_message(chat_id=chat_id, text=f"❗ SYSTEM ERROR:\n{message}")
        except Exception as e:
            print("Failed to send error message:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    await update.message.reply_text("Bot active. Signals will be sent here.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.discard(chat_id)
    await update.message.reply_text("Bot stopped for this chat.")

async def symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_symbols
    if context.args:
        current_symbols = [s.upper() for s in context.args]
        set_kline_symbols(current_symbols)
        init_symbol_data(current_symbols)
        restart_websocket()
        await update.message.reply_text(f"Symbols updated:\n{', '.join(current_symbols)}")
    else:
        await update.message.reply_text("Usage: /symbol BTCUSDT ETHUSDT")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for symbol in current_symbols:
        closes = symbol_data.get(symbol, {}).get("closes", [])
        if len(closes) >= 50:
            text = generate_trend_summary(closes[-50:])
            await update.message.reply_text(f"{symbol} Summary:\n{text}")
        else:
            await update.message.reply_text(f"Not enough data for {symbol} yet.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = f"📌 Active Symbol(s): {', '.join(current_symbols)}\n👥 Active Users: {len(active_chats)}"
    await update.message.reply_text(text)

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for symbol in current_symbols:
        closes = get_symbol_data(symbol).get("closes", [])
        if len(closes) >= 50:
            image = generate_macd_chart(closes[-50:], symbol)
            await update.message.reply_photo(photo=image)
        else:
            await update.message.reply_text(f"Not enough data to generate chart for {symbol}.")

async def dailyreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for symbol in current_symbols:
        closes = symbol_data.get(symbol, {}).get("closes", [])
        if len(closes) >= 50:
            summary = generate_trend_summary(closes[-50:])
            image = generate_macd_chart(closes[-50:], symbol)
            await update.message.reply_photo(photo=image, caption=f"📈 {symbol} Daily Report:\n{summary}")
        else:
            await update.message.reply_text(f"Not enough data to generate daily report for {symbol}.")