!pip install pyrebase4
!pip install python-telegram-bot --upgrade

import pyrebase
from telegram.ext import Application, MessageHandler, filters

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
telegram_token = "7293691754:AAEJOKDyJLX36my4mLIcUJzX24LKzoxx_tE"

# Function to handle incoming messages
async def handle_message(update, context):
    message = update.message.text
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    # Store message in Firebase
    data = {
        "chat_id": chat_id,
        "username": username,
        "message": message
    }
    db.child("messages").push(data)

    # Send confirmation message back to Telegram
    await context.bot.send_message(chat_id=chat_id, text="Message saved to database!")

# Initialize Telegram bot
application = Application.builder().token(telegram_token).build()

# Register message handler
message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
application.add_handler(message_handler)

# Start the bot
application.run_polling()
