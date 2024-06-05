import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
import logging
import asyncio

# Load environment variables
load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
group_usernames = ["nbhsoltracker", "nbhevm"]
defined_bot_username = os.getenv("DEFINED_BOT_USERNAME")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Telethon client
client = TelegramClient("session_name", api_id, api_hash)

# Define a mapping from source group to target group (adjust as needed)
chat_mapping = {
    "nbhsoltracker": "https://t.me/2",  # Replace with actual target chat username or ID
    "nbhevm": "https://t.me/1"  # Replace with actual target chat username or ID
}

@client.on(events.NewMessage(chats=group_usernames))
async def handler(event):
    try:
        sender = await event.get_sender()
        if sender is None:
            logger.error("Failed to get sender information")
            return

        sender_username = sender.username

        # Check if the message is from the Defined Bot
        if sender_username != defined_bot_username:
            logger.info(f"Ignored message from {sender_username}")
            return

        logger.info(f"Received message: {event.message.message} from {sender_username}")

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
        logger.info(f"Message sent to {target_chat}: {message_text}")

        # Delete the copied message (sent from your account)
        await asyncio.sleep(2)  # Give some time for the message to appear
        await sent_message.delete()
        logger.info(f"Message deleted from {target_chat}: {message_text}")

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")

async def main():
    await client.start()
    logger.info("Client Created")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
