import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

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
    keyboard = [
        [InlineKeyboardButton("Dana", callback_data='DANA')],
        [InlineKeyboardButton("OVO", callback_data='OVO')],
        [InlineKeyboardButton("ShopeePay", callback_data='SHP')],
        [InlineKeyboardButton("LinkAja", callback_data='LA')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Pilih layanan e-wallet:', reply_markup=reply_markup)

# Handle button press
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    bank_code = query.data
    query.edit_message_text(text=f"Masukkan nomor rekening untuk {bank_code}")

    context.user_data['selected_bank'] = bank_code

# Handle message with account number
def handle_message(update: Update, context: CallbackContext) -> None:
    bank_code = context.user_data.get('selected_bank')
    if not bank_code:
        update.message.reply_text("Pilih layanan e-wallet terlebih dahulu dengan perintah /start.")
        return

    account_number = update.message.text
    result = check_ewallet(account_number, bank_code)
    update.message.reply_text(result)

# Setup Telegram webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Setup Flask route for health check
@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

if __name__ == "__main__":
    from telegram.ext import Dispatcher

    dispatcher = Dispatcher(bot, None, workers=0)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Set webhook to Vercel's domain
    bot.set_webhook(url=f"https://{os.getenv('VERCEL_URL')}/{TOKEN}")
    app.run(debug=True)
