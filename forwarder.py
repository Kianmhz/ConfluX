import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
import logging
import asyncio

# Load environment variables
load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME")
bot_username = os.getenv("BOT_USERNAME")  # Bot's username, not token
group_username = os.getenv("GROUP_USERNAME")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Telethon client
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=group_username))
async def handler(event):
    me = await client.get_me()
    sender = await event.get_sender()
    sender_id = sender.id
    sender_username = sender.username

    logger.info(f"Received message: {event.message.message} from {sender_id} ({sender_username})")

    # Ensure we are not forwarding our own messages
    if sender_id != me.id:
        message_text = event.message.message
        # Send message to the bot using your personal account
        await client.send_message(bot_username, f"Message from {sender_username}: {message_text}")

async def main():
    await client.start()
    logger.info("Client Created")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
