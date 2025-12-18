import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import re
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

# Load environment variables
load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
group_username = ["Group1", "Group2"]  # List of group usernames to monitor
defined_bot_username = os.getenv("DEFINED_BOT_USERNAME")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set logging levels for specific loggers to avoid unnecessary logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Create the Telethon client
client = TelegramClient("session_name", api_id, api_hash)

# Dictionary to store transactions by contract address
transaction_log = defaultdict(list)
# Set to track contracts with the first confluence ping
first_confluence_contracts = set()

# Timeframe within which to check for coinciding transactions
TIMEFRAME = timedelta(minutes=240)

# Define a mapping from source group to target group (adjust as needed)
chat_mapping = {
    "nbhsoltracker": "https://t.me/nbhsoltracker",  # Replace with actual target chat username or ID
    "nbhevm": "https://t.me/nbhevm"  # Replace with actual target chat username or ID
}

# Periodic cleanup function to remove outdated transactions from memory
async def periodic_cleanup():
    while True:
        current_time = datetime.now()
        
        # Cleanup transaction_log
        for contract_address in list(transaction_log.keys()):
            # Remove outdated transactions for each contract address
            transaction_log[contract_address] = [
                t for t in transaction_log[contract_address] if current_time - t[5] <= TIMEFRAME
            ]
            # If the list is empty, remove the contract address from the log
            if not transaction_log[contract_address]:
                del transaction_log[contract_address]
        
        # Cleanup first_confluence_contracts
        # Remove contract addresses that are no longer in transaction_log
        first_confluence_contracts.intersection_update(transaction_log.keys())

        await asyncio.sleep(600)  # Run cleanup every 10 minutes

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
    global transaction_log, first_confluence_contracts

    message = update.message.text
    timestamp = datetime.now()

    # Regex pattern to extract the necessary information
    pattern = (
        r'(?P<name>\w+).*'                               # Extract the name
        r'Token (?P<transaction_type>Buy|Sell).*'        # Extract the transaction type (Token Buy or Token Sell)
        r'\n(?P<contract_address>\w+).*'                 # Extract the contract address
        r'[⬅️➡️] (?:Sent|Received): [\d,.]+ (?P<received_coin>\w+) - (?P<percentage>[\d,.]+%)'  # Extract the received/sent coin and percentage
        r'.*Mkt\. Cap \(FDV\): \$?(?P<market_cap>[\d,]+)'  # Extract the market cap
    )

    match = re.search(pattern, message, re.DOTALL)

    if match:
        # Extract the matched details
        name = match.group('name')
        transaction_type = match.group('transaction_type')
        contract_address = match.group('contract_address')
        market_cap = match.group('market_cap')
        received_coin = match.group('received_coin')
        percentage = match.group('percentage')

        logger.info(f"Match found: name={name}, transaction_type={transaction_type}, "
                    f"contract_address={contract_address}, market_cap={market_cap}, "
                    f"received_coin={received_coin}, percentage={percentage}")

        # Add transaction to the log for this contract address
        transaction_log[contract_address].append((name, transaction_type, market_cap, received_coin, percentage, timestamp))

        # Check for confluence of buys
        recent_buys = [t for t in transaction_log[contract_address] if t[1] == "Buy"]
        
        if len(recent_buys) > 1:  # Confluence condition
            dex_url = f"https://dexscreener.com/solana/{contract_address}"
            bullx_url = f"https://bullx.io/terminal?chainId=1399811149&address={contract_address}"
            trojan_url = f"https://t.me/solana_trojanbot?start=r-afterhours8-{contract_address}"
            confluence_message = (
                f"{received_coin} | <a href='{dex_url}'>DEX</a> | <a href='{bullx_url}'>Bullx</a> | <a href='{trojan_url}'>Trojan</a>\n"
                f"<code>{contract_address}</code>\n"
            )

            # Add all recent transactions (buys and sells) in order
            for t in transaction_log[contract_address]:
                icon = "🟢" if t[1] == "Buy" else "🔴"
                confluence_message += f"{icon} {t[0]} - {t[4]} -> ${t[2]} mc\n"

            # Add the #first tag only for the first confluence ping
            if contract_address not in first_confluence_contracts:
                # Check for multiple unique buyers only for the first ping
                unique_buyers = set(buy[0] for buy in recent_buys)  # Track unique buyers
                if len(unique_buyers) > 1:  # True confluence for first ping
                    confluence_message += "\n#first"
                    first_confluence_contracts.add(contract_address)  # Mark the first ping
                else:
                    return

            # Send the message with HTML formatting and disable link preview
            await update.message.reply_text(
                confluence_message, parse_mode='HTML', disable_web_page_preview=True
            )

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
        # Start the periodic cleanup in the background
        asyncio.create_task(periodic_cleanup())
        await client.run_until_disconnected()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
