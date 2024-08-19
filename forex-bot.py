import pyrebase
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Firebase configuration (replace with your own)
firebase_config = {
    "apiKey": "AIzaSyAVwNeN6TWHUEamGrOkJmjCkBLFB186N00",   #os.environ.get('apiKey'),
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
telegram_token = "7293691754:AAEJOKDyJLX36my4mLIcUJzX24LKzoxx_tE"   #os.environ.get('token') 

CHANNEL_CHAT_ID = -1001652712429  # Replace with your channel's chat ID

# Currency pairs available for selection
CURRENCY_PAIRS = [
    "US30", "SPX500", "AUS200", "NAS100", "UK100", "JPN225", "AUDUSD",
    "GBPUSD", "USDCAD", "USDJPY", "AUDJPY", "EURUSD", "NZDUSD", "USDCHF",
    "AUDCAD", "GBPJPY", "XAGUSD", "XAUUSD", "XPDUSD", "XPTUSD", "BTCUSD",
    "LTCUSD", "TRXUSD", "ETHUSD", "XMRUSD", "XRPUSD"
]


# Define the start command with a custom keyboard
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[KeyboardButton("Manage Currency Pairs")],
                [KeyboardButton("Get News for Selected Pairs")]]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    await update.message.reply_text('Please choose:',
                                    reply_markup=reply_markup)


# Function to handle messages based on keyboard button text
async def handle_button_click(update: Update,
                              context: CallbackContext) -> None:
    user_message = update.message.text

    if user_message == "Manage Currency Pairs":
        await manage_currency_pairs(update, context)
    elif user_message == "Get News for Selected Pairs":
        await get_recent_news(update, context)


# Function to manage currency pairs (previously the start function)
async def manage_currency_pairs(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    reply_markup = generate_keyboard(user_id)
    await update.message.reply_text(
        'Please select currency pairs (toggle selection):',
        reply_markup=reply_markup)


# Function to generate the inline keyboard with the user's current selections
def generate_keyboard(user_id):
    keyboard = []
    user_selections = db.child("user_preferences").child(
        user_id).get().val() or {}

    for pair in CURRENCY_PAIRS:
        selected = user_selections.get(pair, False)
        button_text = f"{pair} {'✅' if selected else '❌'}"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=pair)])

    keyboard.append([InlineKeyboardButton("Done", callback_data="done")])
    return InlineKeyboardMarkup(keyboard)


# Callback function to handle currency pair selection/unselection
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    selected_pair = query.data

    if selected_pair == "done":
        await query.edit_message_text(text="Selection saved!")
        return

    # Toggle selection in Firebase
    current_selection = db.child("user_preferences").child(user_id).child(
        selected_pair).get().val() or False
    db.child("user_preferences").child(user_id).child(selected_pair).set(
        not current_selection)

    # Update the keyboard to reflect the new selection state
    reply_markup = generate_keyboard(user_id)
    await query.edit_message_text(
        text="Please select currency pairs (toggle selection):",
        reply_markup=reply_markup)


# Function to provide recent news to users
async def get_recent_news(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_selections = db.child("user_preferences").child(
        user_id).get().val() or {}

    for pair in CURRENCY_PAIRS:
        if user_selections.get(pair, False):
            news = db.child("latest_news").child(pair).get().val()
            if news:
                await update.message.reply_text(
                    f"Latest news for {pair}:\n{news}")
            else:
                await update.message.reply_text(f"No recent news for {pair}.")


# Function to capture signals and news from the channel
async def handle_channel_post(update: Update, context: CallbackContext):
    # Check if the message is from the specific channel
    if update.channel_post.chat_id == CHANNEL_CHAT_ID:
        message_text = update.channel_post.text

        # Extract currency pair and signal from the message text
        lines = message_text.split("\n")
        if len(lines) >= 2:
            pair_line = lines[0]
            signal_line = lines[1]

            # Extract the currency pair and signal
            pair = pair_line.split()[0]
            signal = signal_line.split()[0]

            # Store the latest news for the currency pair
            db.child("latest_news").child(pair).set(message_text)

            # Check if any user has selected this currency pair
            users = db.child("user_preferences").get()
            for user in users.each():
                user_id = user.key()
                if db.child("user_preferences").child(user_id).child(
                        pair).get().val():
                    # Get the last signal for this user and pair
                    last_signal = db.child("last_signals").child(
                        user_id).child(pair).get().val()

                    # If the signal has changed, notify the user and update the last signal
                    if last_signal != signal:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"{pair} Signal changed to: {signal}")
                        db.child("last_signals").child(user_id).child(
                            pair).set(signal)
    else:
        # Ignore messages from other channels
        return


# Initialize Telegram bot
application = Application.builder().token(telegram_token).build()

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(
    MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click))

# Start the bot
application.run_polling()
