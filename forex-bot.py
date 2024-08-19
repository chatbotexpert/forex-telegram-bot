import pyrebase
import os
from keep_alive import keep_alive
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Firebase configuration (replace with your own)
firebase_config = {
    "apiKey": "AIzaSyAVwNeN6TWHUEamGrOkJmjCkBLFB186N00",
    "authDomain": "cryptonotifierbot.firebaseapp.com",
    "databaseURL": "https://cryptonotifierbot-default-rtdb.firebaseio.com",
    "projectId": "cryptonotifierbot",
    "storageBucket": "cryptonotifierbot.appspot.com",
    "messagingSenderId": "468288916113",
    "appId": "1:468288916113:web:895cc848dae22cb0244d30"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Telegram bot token (replace with your own)
telegram_token = Dispatcher(Bot(token=os.environ.get('token')))        #"7293691754:AAEJOKDyJLX36my4mLIcUJzX24LKzoxx_tE"

# Currency pairs available for selection
CURRENCY_PAIRS = ["TRXUSD", "XRPUSD", "US30"]

# Function to generate the inline keyboard with the user's current selections
def generate_keyboard(user_id):
    keyboard = []
    user_selections = db.child("user_preferences").child(user_id).get().val() or {}

    for pair in CURRENCY_PAIRS:
        selected = user_selections.get(pair, False)
        button_text = f"{pair} {'✅' if selected else '❌'}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=pair)])

    keyboard.append([InlineKeyboardButton("Done", callback_data="done")])
    return InlineKeyboardMarkup(keyboard)

# Function to start the bot and let users choose currency pairs
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reply_markup = generate_keyboard(user_id)
    await update.message.reply_text('Please select currency pairs (toggle selection):', reply_markup=reply_markup)

# Callback function to handle currency pair selection/unselection
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    selected_pair = query.data

    if selected_pair == "done":
        await query.edit_message_text(text="Selection saved!")
        return

    # Toggle selection in Firebase
    current_selection = db.child("user_preferences").child(user_id).child(selected_pair).get().val() or False
    db.child("user_preferences").child(user_id).child(selected_pair).set(not current_selection)

    # Update the keyboard to reflect the new selection state
    reply_markup = generate_keyboard(user_id)
    await query.edit_message_text(text="Please select currency pairs (toggle selection):", reply_markup=reply_markup)

# Function to capture signals from the channel
async def handle_channel_post(update: Update, context: CallbackContext):
    message_text = update.channel_post.text

    # Extract currency pair and signal from the message text
    lines = message_text.split("\n")
    if len(lines) >= 2:
        pair_line = lines[0]
        signal_line = lines[1]

        # Extract the currency pair and signal
        pair = pair_line.split()[0]
        signal = signal_line.split()[0]

        # Check if any user has selected this currency pair
        users = db.child("user_preferences").get()
        for user in users.each():
            user_id = user.key()
            if db.child("user_preferences").child(user_id).child(pair).get().val():
                # Get the last signal for this user and pair
                last_signal = db.child("last_signals").child(user_id).child(pair).get().val()

                # If the signal has changed, notify the user and update the last signal
                if last_signal != signal:
                    await context.bot.send_message(chat_id=user_id, text=f"{pair} Signal changed to: {signal}")
                    db.child("last_signals").child(user_id).child(pair).set(signal)

# Start the bot
def main() -> None:
    # Initialize Telegram bot
    application = Application.builder().token(telegram_token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post))

    #application.run_polling(allowed_updates=Update.ALL_TYPES)
    application.run_polling()
    

if __name__ == "__main__":
    main()
