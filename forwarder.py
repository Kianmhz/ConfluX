import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
import requests
import logging
import asyncio

# Load environment variables
load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("TELEGRAM_TOKEN")
forward_to_chat_id = os.getenv("CHAT_ID")
group_username = os.getenv("GROUP_USERNAME")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Telethon client
client = TelegramClient('session_name', api_id, api_hash)

async def send_to_bot(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": forward_to_chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    logger.info(f"Forwarded message: {message}")
    logger.info(f"Response: {response.json()}")

@client.on(events.NewMessage(chats=group_username))
async def handler(event):
    sender = await event.get_sender()
    sender_id = sender.id
    sender_username = sender.username

    logger.info(f"Received message: {event.message.message} from {sender_id} ({sender_username})")

    # Forward the message to your bot
    message_text = event.message.message
    await send_to_bot(message_text)

async def main():
    await client.start()
    logger.info("Client Created")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
