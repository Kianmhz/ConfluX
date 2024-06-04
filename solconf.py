import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re
from datetime import datetime, timedelta

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

# Maximum number of transactions to keep in the list
MAX_TRANSACTIONS = 16

# Asynchronous function to handle the /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Hi! I am your confluence bot.')

# Asynchronous function to handle incoming messages
async def handle_message(update: Update, context: CallbackContext):
    global recent_transactions  # Declare recent_transactions as global to modify it within this function

    message = update.message.text

    # Regex pattern to extract the name, transaction type, contract address, market cap, and received coin name
    pattern = (
        r'(?P<name>\w+).*'                               # Extract the name
        r'Token (?P<transaction_type>Buy|Sell).*'        # Extract the transaction type (Token Buy or Token Sell)
        r'\n(?P<contract_address>\w+).*'                 # Extract the contract address
        r'⬅️ Received: [\d,.]+ (?P<received_coin>\w+)'    # Extract the received coin name
        r'.*Mkt\. Cap \(FDV\): \$?(?P<market_cap>[\d,]+)'  # Extract the market cap
    )

    match = re.search(pattern, message, re.DOTALL)

    if match:
        name = match.group('name')
        transaction_type = match.group('transaction_type')
        contract_address = match.group('contract_address')
        market_cap = match.group('market_cap')
        received_coin = match.group('received_coin')

        # Log extracted information
        logger.info(f"Match found: name={name}, transaction_type={transaction_type}, contract_address={contract_address}, market_cap={market_cap}, received_coin={received_coin}")

        # Add to recent transactions
        timestamp = datetime.now()
        recent_transactions.append((name, transaction_type, contract_address, market_cap, received_coin, timestamp))
        logger.info(f"Updated recent_transactions: {recent_transactions}")

        # Remove old entries
        recent_transactions = [transaction for transaction in recent_transactions if timestamp - transaction[5] <= TIMEFRAME]
        logger.info(f"Filtered recent_transactions: {recent_transactions}")

        # Ensure the recent_transactions list doesn't exceed the max limit
        if len(recent_transactions) > MAX_TRANSACTIONS:
            recent_transactions = recent_transactions[-MAX_TRANSACTIONS:]
            logger.info(f"Trimmed recent_transactions: {recent_transactions}")

        # Check for confluence of buys
        buys = []
        for transaction in recent_transactions:
            if transaction[2] == contract_address and transaction[1] == "Buy":
                buys.append(transaction)

        logger.info(f"Buys list: {buys}")

        if len(buys) > 1:
            # Check for sells
            sells = []
            for transaction in recent_transactions:
                if transaction[2] == contract_address and transaction[1] == "Sell":
                    sells.append(transaction)

            logger.info(f"Sells list: {sells}")

            confluence_message = f"Confluence detected!\n{contract_address}\n"
            for transaction in buys:
                confluence_message += f"🟢 {transaction[0]} ({transaction[4]}) -> Market Cap: ${transaction[3]}\n"
            for transaction in sells:
                confluence_message += f"🔴 {transaction[0]} ({transaction[4]}) -> Market Cap: ${transaction[3]}\n"
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
