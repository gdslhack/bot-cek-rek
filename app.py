import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    keyboard = [
        [InlineKeyboardButton("Cek Dana", callback_data='dana')],
        [InlineKeyboardButton("Cek OVO", callback_data='ovo')],
        [InlineKeyboardButton("Cek ShopeePay", callback_data='shopeepay')],
        [InlineKeyboardButton("Cek LinkAja", callback_data='linkaja')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Pilih metode e-wallet yang ingin Anda cek:", reply_markup=reply_markup)

# Handle button presses
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    bank_code_map = {
        'dana': 'DANA',
        'ovo': 'OVO',
        'shopeepay': 'SHOPEEPAY',
        'linkaja': 'LINKAJA'
    }
    
    bank_code = bank_code_map.get(query.data)
    
    if bank_code:
        query.edit_message_text(text=f"Silakan kirim nomor rekening {bank_code} yang ingin Anda cek.")
        context.user_data['bank_code'] = bank_code
    else:
        query.edit_message_text(text="Metode e-wallet tidak dikenali.")

# Handle text messages for account numbers
def receive_number(update: Update, context: CallbackContext) -> None:
    bank_code = context.user_data.get('bank_code')
    if not bank_code:
        update.message.reply_text("Silakan pilih e-wallet terlebih dahulu menggunakan tombol.")
        return
    
    account_number = update.message.text.strip()
    result = check_ewallet(account_number, bank_code)
    update.message.reply_text(result)

# Create dispatcher
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, receive_number))

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
