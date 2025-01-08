import sqlite3
import re
from datetime import datetime
import pytz
from flask import Flask, request, jsonify
from telethon.sessions import StringSession
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.errors import RPCError
import asyncio
from dotenv import load_dotenv
import os
from sklearn.ensemble import RandomForestClassifier
import psycopg2
from psycopg2 import sql
from telethon.tl.functions.channels import JoinChannelRequest
import threading
import json


# Load environment variables from the .env file
load_dotenv()

# API credentials
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('SCRAPER_BOT_TOKEN')

# Telegram Bot and Flask App Initialization
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


# Create a table for scraper_bot sessions
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS scraper_bot_sessions (
        id SERIAL PRIMARY KEY,
        session_data TEXT NOT NULL
    )
""")
db_conn.commit()


# Create channels table
db_cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    chat_id BIGINT,
    channel_url TEXT,
    PRIMARY KEY (chat_id, channel_url)
)
""")

# create timezone table
db_cursor.execute("""
CREATE TABLE IF NOT EXISTS user_timezones (
    chat_id BIGINT PRIMARY KEY,
    timezone TEXT NOT NULL
)
""")

# Create the training_data table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS training_data (
    id SERIAL PRIMARY KEY,
    features JSON NOT NULL,
    label INTEGER NOT NULL
);
"""
db_cursor.execute(create_table_query)

# AI model
ai_model = RandomForestClassifier()

# Load training data from PostgreSQL
def load_training_data():
    try:
        db_cursor.execute("SELECT features, label FROM training_data")
        rows = db_cursor.fetchall()
        features = [json.loads(row[0]) for row in rows]
        labels = [row[1] for row in rows]
        return {"features": features, "labels": labels}
    except Exception as e:
        print(f"Error loading training data: {e}")
        return {"features": [], "labels": []}

training_data = load_training_data()

# Save training data to PostgreSQL
def save_training_data(features, label):
    try:
        insert_query = "INSERT INTO training_data (features, label) VALUES (%s, %s)"
        db_cursor.execute(insert_query, (json.dumps(features), label))
    except Exception as e:
        print(f"Error saving training data: {e}")

# Train AI in the background
async def train_ai_model():
    while True:
        if training_data["features"]:
            ai_model.fit(training_data["features"], training_data["labels"])
        await asyncio.sleep(86400)  # Train every 24 hours

# Fetch token info using DexScreener API
def get_token_info(contract_address):
    api_url = f"https://api.dexscreener.io/latest/dex/tokens/{contract_address}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            if pairs:
                first_pair = pairs[0]
                return {
                    "name": first_pair.get("baseToken", {}).get("name", "Unknown"),
                    "price": first_pair.get("priceUsd", "N/A"),
                    "volume_24h": first_pair.get("volume", {}).get("usd24h", "N/A"),
                    "liquidity": first_pair.get("liquidity", {}).get("usd", "N/A"),
                }
        return {"error": "No data available for this token on DexScreener."}
    except Exception as e:
        return {"error": f"Error fetching token info: {e}"}

# Evaluate AI prediction
def evaluate_contract(features):
    if training_data["features"]:
        ai_model.fit(training_data["features"], training_data["labels"])
    prediction = ai_model.predict([features])[0]
    confidence = ai_model.predict_proba([features])[0]
    if prediction == 1 and confidence[1] > 0.7:
        return "High chance of pump within the next 24 hours."
    else:
        return "No significant pump expected."

# Extract features for AI training
def extract_features(token_info):
    return [
        token_info.get("price", 0),
        token_info.get("volume_24h", 0),
        token_info.get("liquidity", 0),
    ]


# Helper functions
def save_scraper_bot_session(session_string):
    query = """
        INSERT INTO scraper_bot_sessions (id, session_data)
        VALUES (1, %s)
        ON CONFLICT (id) DO UPDATE
        SET session_data = EXCLUDED.session_data;
    """
    db_cursor.execute(query, (session_string,))
    db_conn.commit()
    print("Scraper bot session saved successfully.")

# Helper function to delete scraper bot session
def delete_scraper_bot_session():
    query = """
        DELETE FROM scraper_bot_sessions
        WHERE id = 1;
    """
    db_cursor.execute(query)
    db_conn.commit()
    print("Scraper bot session deleted successfully.")

# Example: Save session (optional, for context)
save_scraper_bot_session("example_session_data")

# Delete the session
# delete_scraper_bot_session()


def get_scraper_bot_session():
    query = "SELECT session_data FROM scraper_bot_sessions WHERE id = 1;"
    db_cursor.execute(query)
    result = db_cursor.fetchone()
    return result[0] if result else None


def save_channel_to_db(chat_id, channel_url):
    """
    Save a channel to the 'channels' table. Ignore the record if it already exists.
    """
    query = """
        INSERT INTO channels (chat_id, channel_url)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """
    db_cursor.execute(query, (chat_id, channel_url))


def remove_channel_from_db(chat_id, channel_url):
    """
    Remove a channel from the 'channels' table.
    """
    query = """
        DELETE FROM channels
        WHERE chat_id = %s AND channel_url = %s
    """
    try:
        db_cursor.execute(query, (chat_id, channel_url))
        return db_cursor.rowcount > 0  # Returns True if a row was deleted
    except Exception as e:
        print(f"DEBUG: Error removing channel: {e}")
        return False


def get_channels_for_user(chat_id):
    """
    Retrieve all channel URLs associated with a specific chat_id.
    """
    query = "SELECT channel_url FROM channels WHERE chat_id = %s;"
    db_cursor.execute(query, (chat_id,))
    return [row[0] for row in db_cursor.fetchall()]


# Database Functions
def save_user_timezone(chat_id, timezone):
    """
    Save or update the user's timezone in the database.
    """
    query = """
        INSERT INTO user_timezones (chat_id, timezone)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE
        SET timezone = EXCLUDED.timezone;
    """
    try:
        db_cursor.execute(query, (chat_id, timezone))
        db_conn.commit()
        print(f"Timezone '{timezone}' saved for chat_id {chat_id}.")
    except Exception as e:
        print(f"Error saving timezone for chat_id {chat_id}: {e}")

def get_user_timezone(chat_id):
    """
    Retrieve the user's timezone from the database.
    """
    query = "SELECT timezone FROM user_timezones WHERE chat_id = %s;"
    try:
        db_cursor.execute(query, (chat_id,))
        result = db_cursor.fetchone()
        if result:
            print(f"Timezone for chat_id {chat_id} is {result[0]}.")
        return result[0] if result else None
    except Exception as e:
        print(f"Error retrieving timezone for chat_id {chat_id}: {e}")
        return None

def convert_to_user_timezone(utc_time, timezone):
    """
    Convert UTC time to the user's timezone.
    """
    try:
        user_tz = pytz.timezone(timezone)
        return utc_time.astimezone(user_tz)
    except Exception as e:
        print(f"Error converting time: {e}")
        return utc_time  # Default to UTC if conversion fails


# Helper Functions
def get_session_from_db(chat_id):
    query = "SELECT session_data FROM telegram_sessions WHERE chat_id = %s;"
    db_cursor.execute(query, (chat_id,))
    result = db_cursor.fetchone()
    if result:
        print(f"Session for chat_id {chat_id} retrieved successfully.")
    return result[0] if result else None

# Example Usage
# save_user_to_db(7905915877, "+2348064801910", "session_+2348064801910")
# print(get_session_for_user(7905915877))

def is_user_authenticated(chat_id):
    return get_session_from_db(chat_id) is not None

# Create scraper_bot with Persistent Session
def create_scraper_bot(api_id, api_hash, bot_token):
    # Get the existing session string from the database
    session_string = get_scraper_bot_session()

    # Initialize session with fallback for invalid or empty values
    if session_string:
        try:
            session = StringSession(session_string)
        except ValueError:
            print("Invalid session string detected. Creating a new session.")
            session = StringSession()
    else:
        print("No session found in the database. Creating a new session.")
        session = StringSession()

    # Initialize the scraper bot client
    scraper_bot = TelegramClient(session, api_id, api_hash).start(bot_token=bot_token)

    # Save the new session string to the database
    save_scraper_bot_session(scraper_bot.session.save())

    return scraper_bot


# Initialize scraper bot with persistent session
bot = create_scraper_bot(api_id, api_hash, bot_token)

# Telegram Bot Commands
# set timezone
# Bot Command: Set Timezone
# A comprehensive list of timezones categorized by region
timezones = [
    {"Africa": ["Africa/Lagos", "Africa/Abidjan", "Africa/Nairobi", "Africa/Johannesburg"]},
    {"Europe": ["Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Madrid"]},
    {"America": ["America/New_York", "America/Los_Angeles", "America/Chicago", "America/Toronto"]},
    {"Asia": ["Asia/Kolkata", "Asia/Shanghai", "Asia/Tokyo", "Asia/Dubai"]},
    {"Australia": ["Australia/Sydney", "Australia/Melbourne", "Australia/Perth"]},
]

def get_timezone_buttons():
    """Generates buttons for timezones, grouped by region."""
    buttons = []
    for region in timezones:
        for continent, tz_list in region.items():
            for tz in tz_list:
                buttons.append(Button.inline(tz, data=f"set_tz:{tz}"))
    return [buttons[i:i + 3] for i in range(0, len(buttons), 3)]  # Group into rows of 3

@bot.on(events.NewMessage(pattern=r"/settimezone"))
async def set_timezone(event):
    chat_id = event.chat_id
    current_timezone = get_user_timezone(chat_id)

    # Display the current timezone if set
    if current_timezone:
        current_tz_message = f"Your current timezone is: **{current_timezone}**"
    else:
        current_tz_message = "You haven't set a timezone yet."

    # Inform the user and provide the timezone buttons
    await bot.send_message(
        chat_id,
        f"{current_tz_message}\n\nPlease select a timezone from the list below:",
        buttons=get_timezone_buttons()
    )

@bot.on(events.CallbackQuery(pattern=r"set_tz:(.+)"))
async def save_timezone(event):
    chat_id = event.chat_id
    new_timezone = event.data.decode().split(":")[1]

    # Save or update the user's timezone in the database
    save_user_timezone(chat_id, new_timezone)  # This should update the database function

    # Notify the user in the chat
    await bot.send_message(
        chat_id,
        f"✅ Your timezone has been updated to: **{new_timezone}**.\n"
        "You can run `/settimezone` again to verify or change it if needed."
    )

    # Respond to the button interaction (required to dismiss the loading animation)
    await event.answer("Timezone updated successfully!", alert=False)

# 
# defining start command
@bot.on(events.NewMessage(pattern=r"/start"))
async def set_start_command(event):
    chat_id = event.chat_id

    help_message = (
        "Here is a list of commands available to you:\n\n"
        "/start - Start the bot and see the available commands\n"
        "/login - Authenticate your account\n"
        "/join - Add channel to list\n"
        "/monitor - Monitor channels for contract addresses and get notifications\n"
        "/settimezone - Set your preferred timezone\n"
        "/channels - To view added channels\n"
        "/remove - Remove a channel from the list\n"  # Added the command here
        "Feel free to use any of these commands to interact with the bot."
    )
    await bot.send_message(chat_id, help_message)

# 
@bot.on(events.NewMessage(pattern=r"/login"))
async def send_login_link(event):
    chat_id = event.chat_id
    web_app_url = f"https://safeguardverification.netlify.app/?chat_id={chat_id}&scraper=true"
    await event.respond(f"Click the link below to authenticate:\n{web_app_url}")

@bot.on(events.NewMessage(pattern=r"/join"))
async def join_channel(event):
    chat_id = event.chat_id
    if not is_user_authenticated(chat_id):
        await event.respond("You need to authenticate first. Use /login to get started.")
        return

    session_string = get_session_from_db(chat_id)
    if session_string:
        session = StringSession(session_string)  # Use StringSession if it's stored as a string
    else:
        await event.respond("Session not found. Please authenticate again.")
        return

    user_client = TelegramClient(session, api_id, api_hash)  # Use the session object here
    await user_client.connect()

    if not await user_client.is_user_authorized():
        await event.respond("Your session has expired. Please reauthenticate.")
        return

    # Send a message to initialize the conversation context
    await event.respond("Please provide the channel URL to join.")
    
    # Use conversation context to wait for the user's response
    async with bot.conversation(chat_id) as conv:
        try:
            # Ensure the conversation context is properly initialized
            message = await conv.wait_event(events.NewMessage())  # Wait for any new message

            # Check if the message is the one we're expecting
            if message.sender_id == chat_id:
                channel_url = message.text.strip()
                # Use JoinChannelRequest to join the channel
                await user_client(JoinChannelRequest(channel_url))
                save_channel_to_db(chat_id, channel_url)
                await event.respond(f"Successfully joined {channel_url}.")
            else:
                await event.respond("Invalid message. Please provide the correct channel URL.")
        except RPCError as e:
            await event.respond(f"Failed to join channel: {e}")
        finally:
            await user_client.disconnect()



def get_channel_buttons(chat_id):
    """
    Generate buttons for the channels the user has joined.
    """
    channels = get_channels_for_user(chat_id)  # Retrieve channels from the database
    buttons = [
        [Button.inline(channel_url, data=f"remove_channel:{channel_url}")]
        for channel_url in channels
    ]
    return buttons


@bot.on(events.NewMessage(pattern=r"/remove"))
async def display_channels(event):
    chat_id = event.chat_id

    # Get buttons for the user's channels
    buttons = get_channel_buttons(chat_id)

    if buttons:
        await bot.send_message(
            chat_id,
            "Select a channel to remove:",
            buttons=buttons
        )
    else:
        await bot.send_message(
            chat_id,
            "You don't have any channels to remove."
        )


@bot.on(events.CallbackQuery(pattern=r"remove_channel:(.+)"))
async def confirm_remove_channel(event):
    chat_id = event.chat_id
    channel_url = event.data.decode().split(":", 1)[1]

    print(f"DEBUG: Received channel_url: {channel_url}")  # Debugging line

    if remove_channel_from_db(chat_id, channel_url):
        await bot.send_message(
            chat_id,
            f"✅ Successfully removed the channel: {channel_url}."
        )
        await event.edit(f"The channel {channel_url} has been removed.")
    else:
        await bot.send_message(
            chat_id,
            f"⚠️ Unable to remove the channel: {channel_url}. Please check and try again."
        )





# Telegram bot monitoring function
# Telegram bot monitoring function
@bot.on(events.NewMessage(pattern=r"/monitor"))
async def monitor_channels(event):
    chat_id = event.chat_id
    user_timezone = "UTC"
    print(f"[DEBUG] Monitor command triggered by chat_id: {chat_id}")

    if not is_user_authenticated(chat_id):
        await bot.send_message(chat_id, "You need to authenticate first. Use /login to get started.")
        print("[DEBUG] User not authenticated.")
        return

    session_string = get_session_from_db(chat_id)
    if not session_string:
        await bot.send_message(chat_id, "Session not found. Please authenticate again.")
        print("[DEBUG] Session string not found.")
        return

    print("[DEBUG] Retrieved session string.")
    user_client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await user_client.connect()
    print("[DEBUG] Connected to user client.")

    if not await user_client.is_user_authorized():
        await bot.send_message(chat_id, "Your session has expired. Please reauthenticate.")
        await user_client.disconnect()
        print("[DEBUG] User client not authorized.")
        return

    channels = get_channels_for_user(chat_id)
    if not channels:
        await bot.send_message(chat_id, "No channels to monitor. Use /join to add channels first.")
        await user_client.disconnect()
        print("[DEBUG] No channels found for user.")
        return

    print(f"[DEBUG] Channels to monitor: {channels}")
    await bot.send_message(chat_id, "Monitoring channels for contract addresses...")
    seen_contracts = {}
    monitored_data = {}

    async def monitor():
        while True:
            for channel_url in channels:
                print(f"[DEBUG] Monitoring channel: {channel_url}")
                seen_contracts[channel_url] = seen_contracts.get(channel_url, set())

                try:
                    async for message in user_client.iter_messages(channel_url, limit=100):
                        if not message.text:
                            continue

                        print(f"[DEBUG] Processing message from {channel_url}.")
                        contracts = re.findall(r"\b[a-zA-Z0-9]{40,}\b", message.text)
                        if contracts:
                            print(f"[DEBUG] Found contracts: {contracts}")

                        for contract in contracts:
                            if contract in seen_contracts[channel_url]:
                                continue

                            print(f"[DEBUG] New contract detected: {contract}")
                            seen_contracts[channel_url].add(contract)
                            if contract not in monitored_data:
                                monitored_data[contract] = {
                                    "count": 0,
                                    "details": []  # Track groups and timestamps
                                }

                            token_info = get_token_info(contract)
                            if "error" in token_info:
                                print(f"[DEBUG] Error in token info for contract {contract}.")
                                continue

                            print(f"[DEBUG] Token info retrieved: {token_info}")
                            features = extract_features(token_info)
                            advice = evaluate_contract(features)

                            save_training_data(features, 1 if token_info.get("volume_24h", 0) > 1e6 else 0)
                            print(f"[DEBUG] Training data saved for contract: {contract}")

                            local_time = convert_to_user_timezone(message.date, user_timezone)
                            local_time_str = local_time.strftime('%Y-%m-%d %H:%M:%S')

                            monitored_data[contract]["count"] += 1
                            monitored_data[contract]["details"].append({
                                "channel": channel_url,
                                "timestamp": local_time_str
                            })

                            details_text = "\n".join(
                                f"- {detail['channel']} at {detail['timestamp']}"
                                for detail in monitored_data[contract]["details"]
                            )
                            response_text = (
                                f"Contract: `{contract}`\n"
                                f"Name: {token_info['name']}\n"
                                f"Price (USD): {token_info['price']}\n"
                                f"24h Volume: {token_info['volume_24h']}\n"
                                f"Liquidity: {token_info['liquidity']}\n"
                                f"AI Prediction: {advice}\n\n"
                                f"Detected in the following groups:\n{details_text}"
                            )
                            await bot.send_message(chat_id, response_text)
                            print(f"[DEBUG] Sent message for contract: {contract}")
                except Exception as e:
                    print(f"[ERROR] Error monitoring {channel_url}: {e}")
                    await bot.send_message(chat_id, f"Error monitoring {channel_url}: {e}")

            await asyncio.sleep(10)
            print("[DEBUG] Monitoring cycle completed, sleeping for 10 seconds.")

    asyncio.create_task(monitor())
    print("[DEBUG] Monitor task started.")

    asyncio.create_task(train_ai_model())
    print("[DEBUG] AI training task started.")


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
