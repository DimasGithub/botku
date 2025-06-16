from telegram.ext import ApplicationBuilder, CommandHandler
from telegram_bot.bot import (
    start,
    stop,
    symbol,
    summary,
    status,
    chart,
    dailyreport,
    current_symbols,
    init_symbol_data,
    set_kline_symbols,
    start_websocket,
    send_telegram_message,
    send_telegram_error_message,
)
from config.settings import TELEGRAM_TOKEN

if __name__ == "__main__":
    set_kline_symbols(current_symbols)
    init_symbol_data(current_symbols)
    start_websocket(send_telegram_error_message)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("symbol", symbol))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("dailyreport", dailyreport))

    print("🤖 Telegram bot running...")
    app.run_polling()
