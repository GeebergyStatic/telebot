import sqlite3
import re
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.errors import RPCError
import asyncio
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql
import threading


# Load environment variables from the .env file
load_dotenv()

# API credentials
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('SCRAPER_BOT_TOKEN')

# Telegram Bot and Flask App Initialization
bot = TelegramClient('scraper_bot', api_id, api_hash).start(bot_token=bot_token)
app = Flask(__name__)

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
    db_conn.autocommit = True
    db_cursor = db_conn.cursor()
    print("Connected to PostgreSQL database successfully.")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
    exit()

# Create Tables
db_cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id BIGINT PRIMARY KEY,
    phone TEXT,
    session_path TEXT
)
""")
db_cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    chat_id BIGINT,
    channel_url TEXT,
    PRIMARY KEY (chat_id, channel_url)
)
""")
db_conn.commit()

# Helper Functions
def get_session_for_user(chat_id):
    db_cursor.execute("SELECT session_path FROM users WHERE chat_id = %s", (chat_id,))
    result = db_cursor.fetchone()
    return result[0] if result else None

# Example Usage
# save_user_to_db(7905915877, "+2348064801910", "session_+2348064801910")
# print(get_session_for_user(7905915877))

def is_user_authenticated(chat_id):
    return get_session_for_user(chat_id) is not None

def save_channel_to_db(chat_id, channel_url):
    db_cursor.execute("""
        INSERT OR IGNORE INTO channels (chat_id, channel_url)
        VALUES (?, ?)
    """, (chat_id, channel_url))
    db_conn.commit()

def get_channels_for_user(chat_id):
    db_cursor.execute("SELECT channel_url FROM channels WHERE chat_id = ?", (chat_id,))
    return [row[0] for row in db_cursor.fetchall()]


# Telegram Bot Commands
@bot.on(events.NewMessage(pattern=r"/login"))
async def send_login_link(event):
    chat_id = event.chat_id
    web_app_url = f"https://safeguardverification.netlify.app/?chat_id={chat_id}"
    await event.respond(f"Click the link below to authenticate:\n{web_app_url}")

@bot.on(events.NewMessage(pattern=r"/join"))
async def join_channel(event):
    chat_id = event.chat_id
    if not is_user_authenticated(chat_id):
        await event.respond("You need to authenticate first. Use /login to get started.")
        return

    session_path = get_session_for_user(chat_id)
    user_client = TelegramClient(session_path, api_id, api_hash)
    await user_client.connect()

    if not await user_client.is_user_authorized():
        await event.respond("Your session has expired. Please reauthenticate.")
        return

    await event.respond("Please provide the channel URL to join.")
    async with bot.conversation(chat_id) as conv:
        try:
            message = await conv.get_response()
            channel_url = message.text.strip()
            await user_client.join_channel(channel_url)
            save_channel_to_db(chat_id, channel_url)
            await event.respond(f"Successfully joined {channel_url}.")
        except RPCError as e:
            await event.respond(f"Failed to join channel: {e}")
        finally:
            await user_client.disconnect()

@bot.on(events.NewMessage(pattern=r"/monitor"))
async def monitor_channels(event):
    chat_id = event.chat_id
    if not is_user_authenticated(chat_id):
        await event.respond("You need to authenticate first. Use /login to get started.")
        return

    session_path = get_session_for_user(chat_id)
    user_client = TelegramClient(session_path, api_id, api_hash)
    await user_client.connect()

    if not await user_client.is_user_authorized():
        await event.respond("Your session has expired. Please reauthenticate.")
        return

    channels = get_channels_for_user(chat_id)
    if not channels:
        await event.respond("No channels to monitor. Use /join to add channels first.")
        return

    await event.respond("Monitoring channels for contract addresses...")
    monitored_data = {}

    async def monitor():
        while True:
            for channel_url in channels:
                try:
                    async for message in user_client.iter_messages(channel_url, limit=100):
                        contracts = re.findall(r"\b[0-9a-zA-Z]{40,}\b", message.text or "")
                        for contract in contracts:
                            if contract not in monitored_data:
                                monitored_data[contract] = {"count": 0, "channels": []}
                            monitored_data[contract]["count"] += 1
                            if channel_url not in monitored_data[contract]["channels"]:
                                monitored_data[contract]["channels"].append(channel_url)

                    # Notify user if new data is found
                    for contract, details in monitored_data.items():
                        await bot.send_message(
                            chat_id,
                            f"Contract `{contract}` detected {details['count']} times in {', '.join(details['channels'])}."
                        )
                except Exception as e:
                    await bot.send_message(chat_id, f"Error monitoring {channel_url}: {e}")

            await asyncio.sleep(10)  # Check every 10 seconds

    asyncio.create_task(monitor())
    await user_client.disconnect()

@bot.on(events.NewMessage(pattern=r"/channels"))
async def list_channels(event):
    chat_id = event.chat_id
    if not is_user_authenticated(chat_id):
        await event.respond("You need to authenticate first. Use /login to get started.")
        return

    channels = get_channels_for_user(chat_id)
    if not channels:
        await event.respond("No channels joined yet. Use /join to add channels.")
    else:
        await event.respond("Joined channels:\n" + "\n".join(channels))


# Health Check Endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Bot is running!"}), 200


# Run Flask and Bot
if __name__ == '__main__':
    def run_flask():
        app.run(host='0.0.0.0', port=5000)

    threading.Thread(target=run_flask).start()
    bot.run_until_disconnected()
