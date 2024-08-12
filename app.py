import os
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

# Define states for the conversation
CHOOSE_METHOD, GET_ACCOUNT_NUMBER = range(2)

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

# Start conversation
def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Cek Dana", callback_data='DANA')],
        [InlineKeyboardButton("Cek OVO", callback_data='OVO')],
        [InlineKeyboardButton("Cek ShopeePay", callback_data='SHOPEEPAY')],
        [InlineKeyboardButton("Cek LinkAja", callback_data='LINKAJA')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Pilih metode e-wallet yang ingin Anda cek:", reply_markup=reply_markup)
    return CHOOSE_METHOD

# Handle button presses
def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    # Save chosen method in user data
    context.user_data['method'] = query.data
    query.edit_message_text(text="Silakan kirim nomor rekening yang ingin Anda cek.")
    return GET_ACCOUNT_NUMBER

# Handle account number input
def receive_account_number(update: Update, context: CallbackContext) -> int:
    account_number = update.message.text
    method = context.user_data.get('method')
    
    # Placeholder account codes
    account_info = {
        'DANA': 'DANA_CODE',
        'OVO': 'OVO_CODE',
        'SHOPEEPAY': 'SHOPEEPAY_CODE',
        'LINKAJA': 'LINKAJA_CODE'
    }
    
    bank_code = account_info.get(method)
    if not bank_code:
        update.message.reply_text("Metode e-wallet tidak dikenali.")
        return ConversationHandler.END

    result = check_ewallet(account_number, bank_code)
    update.message.reply_text(result)
    return ConversationHandler.END

# Create dispatcher and add handlers
dispatcher = Dispatcher(bot, None, workers=0)

# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(button)],
    states={
        CHOOSE_METHOD: [MessageHandler(Filters.text & ~Filters.command, receive_account_number)],
        GET_ACCOUNT_NUMBER: [MessageHandler(Filters.text & ~Filters.command, receive_account_number)],
    },
    fallbacks=[]
))

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
