import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

app = Flask(__name__)

# Function to check e-wallet account
def check_ewallet(account_number: str, bank_code: str):
    url = f"https://cek-rekening-olive.vercel.app/cek-rekening?bankCode={bank_code}&accountNumber={account_number}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["status"]:
            return f"Nama Akun: {data['data']['accountname']}\nBank: {data['data']['bankcode']}"
        else:
            return "Gagal mengambil data. Pastikan nomor rekening benar."
    return "Gagal menghubungi server."

# Command /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Halo! Kirim /cek <bank_code> <account_number> untuk cek nama pengguna e-wallet.")

# Command /cek
def cek(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        update.message.reply_text("Penggunaan: /cek <bank_code> <account_number>")
        return

    bank_code, account_number = context.args
    result = check_ewallet(account_number, bank_code)
    update.message.reply_text(result)

# Handle incoming webhook updates
def handle_update(update: Update) -> None:
    dispatcher.process_update(update)

# Setup Telegram webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    handle_update(update)
    return "ok"

# Setup Flask route for health check
@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

if __name__ == "__main__":
    # Create dispatcher and add handlers
    dispatcher = Dispatcher(bot, None, workers=0)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("cek", cek))
    
    # Set webhook to Vercel's domain
    bot.set_webhook(url=f"https://{os.getenv('VERCEL_URL')}/{TOKEN}")
    
    app.run(debug=True)
