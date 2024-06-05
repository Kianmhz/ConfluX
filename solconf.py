import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import re
import asyncio
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
group_username = ["nbhsoltracker", "nbhevm"]
defined_bot_username = os.getenv("DEFINED_BOT_USERNAME")
shuriken_bot_username = "https://t.me/ShurikenTradeBot"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set logging levels for specific loggers to avoid unnecessary logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Create the Telethon client
client = TelegramClient("session_name", api_id, api_hash)

# Global list to store recent transactions
recent_transactions = []

# Timeframe within which to check for coinciding transactions
TIMEFRAME = timedelta(minutes=240)

# Define a mapping from source group to target group (adjust as needed)
chat_mapping = {
    "nbhsoltracker": "https://t.me/nbhsoltracker",  # Replace with actual target chat username or ID
    "nbhevm": "https://t.me/nbhevm"  # Replace with actual target chat username or ID
}

@client.on(events.NewMessage(chats=group_username))
async def handler(event):
    try:
        sender = await event.get_sender()
        if sender is None:
            return

        sender_username = sender.username

        # Check if the message is from the Defined Bot
        if sender_username != defined_bot_username:
            return

        # Identify the source chat
        source_chat = event.chat.username

        # Determine the target chat based on the source chat
        target_chat = chat_mapping.get(source_chat)
        if not target_chat:
            logger.error(f"No mapping found for source chat: {source_chat}")
            return

        # Copy the message from Defined Bot and send it as if from your account
        message_text = event.message.message
        sent_message = await client.send_message(target_chat, message_text)
        logger.info(f"Message sent to {target_chat}")

        # Delete the copied message (sent from your account)
        await asyncio.sleep(2)  # Give some time for the message to appear
        await sent_message.delete()

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")

# Asynchronous function to handle the /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Hi! I am your confluence bot.')

# Asynchronous function to handle the /chat_id command
async def chat_id(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID: {chat_id}")

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

        # Remove old entries
        recent_transactions = [transaction for transaction in recent_transactions if timestamp - transaction[5] <= TIMEFRAME]

        # Check for confluence of buys
        buys = []
        for transaction in recent_transactions:
            if transaction[2] == contract_address and transaction[1] == "Buy":
                buys.append(transaction)


        if len(buys) > 1:
            if len(buys) == 2:
                await client.send_message(shuriken_bot_username, contract_address)
            # Check for sells
            sells = []
            for transaction in recent_transactions:
                if transaction[2] == contract_address and transaction[1] == "Sell":
                    sells.append(transaction)


            confluence_message = f"Confluence detected!\n{contract_address}\n"
            for transaction in buys:
                confluence_message += f"🟢 {transaction[0]} ({transaction[4]}) -> Market Cap: ${transaction[3]}\n"
            for transaction in sells:
                confluence_message += f"🔴 {transaction[0]} ({transaction[4]}) -> Market Cap: ${transaction[3]}\n"
            await update.message.reply_text(confluence_message)
    else:
        logger.info("No match found.")

# Initialize and start the bot
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Register the /start command handler
application.add_handler(CommandHandler("start", start))

# Register the /chat_id command handler
application.add_handler(CommandHandler("chat_id", chat_id))

# Register the message handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def main():
    # Start the Telethon client
    await client.start()
    logger.info("Client Created")

    # Run the Telegram bot
    async with application:
        await application.start()
        await application.updater.start_polling()
        await client.run_until_disconnected()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())