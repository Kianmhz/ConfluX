import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime, timedelta
import re

# Load environment variables from .env file
load_dotenv()

# Enable logging to a file with UTF-8 encoding
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set logging levels for specific loggers to avoid unnecessary logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Global list to store recent transactions
recent_transactions = []

# Timeframe within which to check for coinciding transactions (e.g., 5 minutes)
TIMEFRAME = timedelta(minutes=240)

# Parsing function
def parse_message(message):
    pattern = (
        r'(?P<name>\w+).*'                       # Extract the name
        r'Token (?P<transaction_type>Buy|Sell)'  # Extract the transaction type (Token Buy or Token Sell)
        r'.*\n(?P<contract_address>\w+).*'       # Extract the contract address
        r'.*Mkt\. Cap \(FDV\): \$?(?P<market_cap>[\d,]+)'  # Extract the market cap
    )

    match = re.search(pattern, message, re.DOTALL)
    if match:
        name = match.group('name')
        transaction_type = match.group('transaction_type')
        contract_address = match.group('contract_address')
        market_cap = match.group('market_cap')
        return {
            'name': name,
            'transaction_type': transaction_type,
            'contract_address': contract_address,
            'market_cap': market_cap
        }
    else:
        return None

# Asynchronous function to handle the /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Hi! I am your confluence bot.')

# Asynchronous function to handle incoming messages
async def handle_message(update: Update, context: CallbackContext):
    global recent_transactions  # Declare recent_transactions as global to modify it within this function

    message = update.message.text

    parsed_data = parse_message(message)
    if parsed_data:
        name = parsed_data['name']
        transaction_type = parsed_data['transaction_type']
        contract_address = parsed_data['contract_address']
        market_cap = parsed_data['market_cap']

        # Log extracted information
        logger.info(f"Match found: name={name}, transaction_type={transaction_type}, contract_address={contract_address}, market_cap={market_cap}")

        # Add to recent transactions
        timestamp = datetime.now()
        recent_transactions.append((name, transaction_type, contract_address, market_cap, timestamp))
        logger.info(f"Updated recent_transactions: {recent_transactions}")

        # Remove old entries
        recent_transactions = [transaction for transaction in recent_transactions if timestamp - transaction[4] <= TIMEFRAME]
        logger.info(f"Filtered recent_transactions: {recent_transactions}")

        # Check for confluence of buys
        buys = []
        for transaction in recent_transactions:
            if transaction[2] == contract_address and transaction[1] == "Buy":
                buys.append(transaction[0])

        logger.info(f"Buys list: {buys}")

        if len(buys) > 1:
            # Check for sells
            sells = []
            for transaction in recent_transactions:
                if transaction[2] == contract_address and transaction[1] == "Sell":
                    sells.append(transaction[0])

            logger.info(f"Sells list: {sells}")

            confluence_message = f"Confluence detected!\n{contract_address}\n"
            for wallet in buys:
                confluence_message += f"🟢 {wallet} -> Market Cap: ${market_cap}\n"
            for wallet in sells:
                confluence_message += f"🔴 {wallet} -> Market Cap: ${market_cap}\n"
            await update.message.reply_text(confluence_message)
    else:
        logger.info("No match found.")

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
