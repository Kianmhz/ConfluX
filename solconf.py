import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global list to store recent buys
recent_buys = []

# Timeframe within which to check for coinciding buys (e.g., 5 minutes)
TIMEFRAME = timedelta(minutes=5)

# Function to handle the /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Hi! I am your confluence bot.')

# Function to handle incoming messages
async def handle_message(update: Update, context: CallbackContext):
    global recent_buys  # Declare recent_buys as global to modify it within this function

    message = update.message.text

    # Regex pattern to extract wallet, coin, and timestamp
    pattern = r'Sent \d+\.\d+ (\w+) .* Received \d+\.\d+ (\w+)'
    match = re.search(pattern, message)
    
    if match:
        wallet = match.group(1)
        coin = match.group(2)
        timestamp = datetime.now()

        # Add to recent buys
        recent_buys.append((wallet, coin, timestamp))

        # Remove old entries
        recent_buys = [buy for buy in recent_buys if timestamp - buy[2] <= TIMEFRAME]

        # Check for confluence
        wallets = set()
        for buy in recent_buys:
            if buy[1] == coin:
                wallets.add(buy[0])

        if len(wallets) > 1:
            await update.message.reply_text(f'Confluence detected! Wallets {wallets} bought {coin} within the last {TIMEFRAME} minutes.')

# Load the bot token from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    logger.error("No TELEGRAM_TOKEN found. Please set it in the environment.")
    exit(1)

# Initialize and start the bot
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Register the /start command handler
application.add_handler(CommandHandler("start", start))

# Register the message handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Start the Bot
application.run_polling()
