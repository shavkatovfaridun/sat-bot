import threading

workers = 1
bind = "0.0.0.0:10000"


def post_fork(server, worker):
    from telegram_bot_web import run_telegram_bot
    threading.Thread(target=run_telegram_bot, daemon=True).start()
