from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User  # Explicitly import User
import asyncio


# Initialize the Telegram client
client = TelegramClient('session_name', api_id, api_hash)

async def main():
        # Start the client without automatic login
        print("Initializing Telegram client...")
        await client.connect()

        # Check if the client is already authorized
        if not await client.is_user_authorized():
            print("Client not authorized. Proceeding with manual login.")
            phone = input("Enter your phone number (with country code): ")
        
            # Request login code
            try:
                login_token = await client.send_code_request(phone)
                print(f"Login code sent to {phone}.")
            except Exception as e:
                print(f"Error sending login code: {e}")
                return

            # Input the login code
            code = input("Enter the code you received: ")
            try:
                user_or_token = await client.sign_in(phone, code)
            
                # Handle 2FA password if needed
                if isinstance(user_or_token, User):
                    print("Successfully logged in as:", user_or_token.username or user_or_token.phone)
                else:
                    print("Two-factor authentication required.")
                    password = input("Enter your 2FA password: ")
                    await client.check_password(password)
                    print("Successfully logged in after entering 2FA password.")
            except SessionPasswordNeededError:
                password = input("Enter your 2FA password: ")
                await client.check_password(password)
                print("Successfully logged in after entering 2FA password.")
            except Exception as e:
                print(f"Error during login: {e}")
                return

        print("Logged in successfully!")

        bot_username = '@helenus_trojanbot'  # Replace with the actual bot username

        # Send a message to the bot to initiate the conversation
        print(f"Sending message to {bot_username}: /start")
        message = await client.send_message(bot_username, '/start')

        # Wait a bit for the bot to respond
        print("Waiting for response after /start...")
        await asyncio.sleep(2)  # Adding a delay to wait for the bot's response

        # Fetch the latest messages from the bot
        response = await client.get_messages(bot_username, limit=5)

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
                    async for message in client.iter_messages(bot_username, limit=10):
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
                                        solana_response = await client.get_messages(bot_username, limit=1)
                                        print(f"Response after clicking 'Solana': {solana_response[0].text}")

                                        # Now look for the 'SOL' button in the new message
                                        async for new_message in client.iter_messages(bot_username, limit=10):
                                            if new_message.buttons:
                                                print("New buttons after Solana click:")
                                                for row in new_message.buttons:
                                                    for button in row:
                                                        print(f"Button text: {button.text}")
                                                        if 'sol' in button.text.lower():  # Case-insensitive match for 'SOL'
                                                            print(f"Clicking the 'SOL' button: {button.text}")
                                                            await button.click()

                                                            # Capture the response after clicking 'SOL'
                                                            final_response = await client.get_messages(bot_username, limit=1)
                                                            print(f"Final response after clicking 'SOL': {final_response[0].text}")

                                                            # Look for the '50 %' button in the new message
                                                            async for next_message in client.iter_messages(bot_username, limit=10):
                                                                if next_message.buttons:
                                                                    print("New buttons after SOL click:")
                                                                    for row in next_message.buttons:
                                                                        for button in row:
                                                                            print(f"Button text: {button.text}")
                                                                            if '50 %' in button.text:  # Case-insensitive match for '100%'
                                                                                print(f"Clicking the '50 %' button: {button.text}")
                                                                                await button.click()

                                                                                # Capture the response after clicking '50 %'
                                                                                response_after_100 = await client.get_messages(bot_username, limit=1)
                                                                                print(f"Response after clicking '50 %': {response_after_100[0].text}")

                                                                                # Now look for the 'Set Withdrawal Address' button
                                                                                async for next_buttons_message in client.iter_messages(bot_username, limit=10):
                                                                                    if next_buttons_message.buttons:
                                                                                        print("New buttons after 50 % click:")
                                                                                        for row in next_buttons_message.buttons:
                                                                                            for button in row:
                                                                                                print(f"Button text: {button.text}")
                                                                                                if 'set withdrawal address' in button.text.lower():  # Case-insensitive match for 'Set Withdrawal Address'
                                                                                                    print(f"Clicking the 'Set Withdrawal Address' button: {button.text}")
                                                                                                    await button.click()

                                                                                                    # Capture the final response after clicking 'Set Withdrawal Address'
                                                                                                    final_withdrawal_response = await client.get_messages(bot_username, limit=1)
                                                                                                    print(f"Final response after clicking 'Set Withdrawal Address': {final_withdrawal_response[0].text}")

                                                                                                    # Send user-defined message (e.g., withdrawal address)
                                                                                                    withdrawal_address = 'D4uqqnayAW2t8iCTChGjEQCnAPx2ukWmitMbDuwYvWf7'  # Replace with the actual address
                                                                                                    print(f"Sending withdrawal address: {withdrawal_address}")
                                                                                                    await client.send_message(bot_username, withdrawal_address)

                                                                                                    # Introduce a delay after sending the withdrawal address
                                                                                                    print("Waiting for 5 seconds after sending withdrawal address...")
                                                                                                    await asyncio.sleep(5)  # Add a 5-second delay

                                                                                                    # Wait for the 'WITHDRAW' button after sending the withdrawal address
                                                                                                    async for final_message in client.iter_messages(bot_username, limit=10):
                                                                                                        print(f"Final message after sending address: {final_message.text}")
                                                                                                        if final_message.buttons:
                                                                                                            for row in final_message.buttons:
                                                                                                                for button in row:
                                                                                                                    print(f"Button text: {button.text}")
                                                                                                                    if 'withdraw' in button.text.lower():  # Specific match for 'WITHDRAW'
                                                                                                                        print(f"Clicking the 'WITHDRAW' button: {button.text}")
                                                                                                                        # await button.click()  
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

# Run the main function
asyncio.run(main())
