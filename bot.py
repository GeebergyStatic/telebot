import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import aiohttp  # Asynchronous HTTP requests
from backend import clients
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# External API endpoint to call (Flask server endpoint)
FLASK_API_URL = 'http://localhost:5000/get_phone_by_sender_id'  # Replace with your Flask API endpoint
API_URL = 'http://localhost:5000/send_message'  # Replace with your API endpoint

# Event handler for /start command
@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):

    # Call Flask API to get the phone number by sender_id
    try:
        # await event.respond("Could not retrieve the phone number.")
        await event.respond(
            file='https://via.placeholder.com/150',  # Path to the image or image URL
            message="Verify your account.",
            buttons=[
                [Button.url("Verify", "https://www.example1.com")],
                [Button.url("@SOLTRENDING", "https://t.me/SOLTRENDING")]  # Button with a URL link
            ]
        )
        return
        


    except Exception as e:
        await event.respond(f"Error fetching phone number: {e}")


# Function to retrieve phone number from Flask API based on sender_id
async def get_phone_by_sender_id(sender_id):
    async with aiohttp.ClientSession() as session:
        try:
            params = {'sender_id': sender_id}
            async with session.get(FLASK_API_URL, params=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data.get('phone', None)
                else:
                    print(f"Error from Flask API: {response.status}")
                    return None
        except Exception as e:
            print(f"Failed to call Flask API: {e}")
            return None


# Function to call the external API (e.g., sending a message)
async def call_external_endpoint(user_client):
    async with aiohttp.ClientSession() as session:
        try:
            # Prepare the data you want to send to the API
            data = {
                'phone': user_client.phone,  # Send the phone number as expected by the API
            }
            async with session.post(API_URL, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return f"Response from API: {response_data.get('message', 'Success!')}"
                else:
                    return f"Error from API: {response.status}"
        except Exception as e:
            return f"Failed to call API: {e}"


# Running the bot
async def main():
    await bot_client.start()
    print("Bot is running...")
    await bot_client.run_until_disconnected()

# Run the bot
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
