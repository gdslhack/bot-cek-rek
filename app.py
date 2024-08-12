import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler

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
        [InlineKeyboardButton("Cek Dana", callback_data='dana')],
        [InlineKeyboardButton("Cek OVO", callback_data='ovo')],
        [InlineKeyboardButton("Cek ShopeePay", callback_data='shopeepay')],
        [InlineKeyboardButton("Cek LinkAja", callback_data='linkaja')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Pilih metode e-wallet yang ingin Anda cek:", reply_markup=reply_markup)

# Command /cek
def cek(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        update.message.reply_text("Penggunaan: /cek <bank_code> <account_number>")
        return

    bank_code, account_number = context.args
    result = check_ewallet(account_number, bank_code)
    update.message.reply_text(result)

# Handle button presses
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # Placeholder account numbers and bank codes
    account_info = {
        'dana': ('1234567890', 'DANA_CODE'),
        'ovo': ('0987654321', 'OVO_CODE'),
        'shopeepay': ('1122334455', 'SHOPEEPAY_CODE'),
        'linkaja': ('5566778899', 'LINKAJA_CODE')
    }
    
    bank_code, account_number = account_info.get(query.data, (None, None))
    if not bank_code or not account_number:
        query.edit_message_text(text="Metode e-wallet tidak dikenali.")
        return
    
    result = check_ewallet(account_number, bank_code)
    query.edit_message_text(text=result)

# Create dispatcher
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("cek", cek))
dispatcher.add_handler(CallbackQueryHandler(button))

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
    # Set webhook to Vercel's domain
    bot.set_webhook(url=f"https://{os.getenv('VERCEL_URL')}/{TOKEN}")
    app.run(debug=True)
