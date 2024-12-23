from telethon import TelegramClient

# Replace these with your Telegram API credentials
api_id = '24353464'
api_hash = 'e12d645e83fda79a60a87ae59e34125b'
phone_number = '+2348064801910'

# Initialize the Telegram client
client = TelegramClient('session_name', api_id, api_hash)

async def main():
    # Start the client and log in
    print("Logging in to Telegram...")
    await client.start(phone=phone_number)
    print("Logged in successfully!")

# Run the client
with client:
    client.loop.run_until_complete(main())
