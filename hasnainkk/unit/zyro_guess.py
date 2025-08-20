from hasnainkk import *
from html import escape
from motor.motor_asyncio import AsyncIOMotorClient
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

async def guessz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check cooldown
    if await check_cooldown(user_id):
        remaining_time = await get_remaining_cooldown(user_id)
        return

    # Initialize `last_characters` if not done yet
    if chat_id not in last_characters:
        last_characters[chat_id] = {}  # Initialize with an empty dictionary

    # Ensure 'name' key exists for this chat_id
    if 'name' not in last_characters[chat_id]:
        return

    # Handle runaway flag
    if last_characters[chat_id].get('ranaway', False):
        return
        
    # Fetch or initialize message_id
    message_id = last_characters[chat_id].get('message_id')
    if not message_id:
        last_characters[chat_id]['message_id'] = None

    guess = update.message.text.lower()

    # Invalid guess handling
    if "()" in guess or "&" in guess.lower():
        return

    # Check if a correct guess has already been made for this chat
    if chat_id in first_correct_guesses:
        return

    # Split and compare name parts
    name_parts = last_characters[chat_id]['name'].lower().split()
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id

        # Cancel any previous expiration tasks
        for task in asyncio.all_tasks():
            if task.get_name() == f"expire_session_{chat_id}":
                task.cancel()
                break

        # Calculate time taken
        timestamp = last_characters[chat_id].get('timestamp')
        time_taken_str = "Unknown time"
        if timestamp:
            time_taken = time.time() - timestamp
            time_taken_str = f"{int(time_taken)} seconds"

        # Update user data in the database
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        # React to the message (optional)
        await react_to_message(chat_id, update.message.id)

        # Add coins to the user's balance
        user = await user_collection.find_one({'id': user_id})
        if user:
            current_balance = user.get('balance', 0)
            new_balance = current_balance + 40
            await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})
            
            await update.message.reply_text(
                f"🎉 Congratulations! You have earned 40 coins for guessing correctly! \nYour new balance is {new_balance} coins."
            )
        else:
            # If the user doesn't exist, create a new user with 40 coins
            await user_collection.insert_one({'id': user_id, 'balance': 40})
            await update.message.reply_text(
                "🎉 Congratulations! You have earned 40 coins for guessing correctly! \nYour new balance is 40 coins."
            )

        # Send a message with character details
        keyboard = [[InlineKeyboardButton("See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(
            f'🌟 <b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b>, you\'ve captured a new character! 🎊\n\n'
            f'📛 𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n'
            f'🌈 𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n'
            f'✨ 𝗥𝗔𝗥𝗜𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\n'
            f'⏱️ 𝗧𝗜𝗠𝗘 𝗧𝗔𝗞𝗘𝗡: <b>{time_taken_str}</b>',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
