from hasnainkk import *
from hasnainkk import application
from html import escape
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram import enums
from motor.motor_asyncio import AsyncIOMotorClient

@app.on_message(filters.command(["guess", "snatch", "collect", "grab", "hunt"]), group=99818887179)
async def guess(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if await check_cooldown(user_id):
        remaining_time = await get_remaining_cooldown(user_id)
        await message.reply_text(
            f"⚠️ You are still in cooldown. Please wait {remaining_time} seconds before using any commands."
        )
        return

    if 'name' not in last_characters.get(chat_id, {}):
        await message.reply_text("❌ character Guess not available")
        return
    
    if chat_id not in last_characters:
        await message.reply_text("❌ character Guess not available")
        return

    if chat_id in first_correct_guesses:
        await message.reply_text("❌ character Guess not available")
        return

    if last_characters[chat_id].get('ranaway', False):
        await message.reply_text("❌ THE CHARACTER HAS ALREADY RUN AWAY!")
        return 

    guess = ' '.join(message.command[1:]).lower() if len(message.command) > 1 else ''
    
    if "()" in guess or "&" in guess.lower():
        await message.reply_text("Nahh You Can't use This Types of words in your guess..❌️")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()
    
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        for task in asyncio.all_tasks():
            if task.get_name() == f"expire_session_{chat_id}":
                task.cancel()
                break

        timestamp = last_characters[chat_id].get('timestamp')
        if timestamp:
            time_taken = time.time() - timestamp
            time_taken_str = f"{int(time_taken)} seconds"
        else:
            time_taken_str = "Unknown time"
        
        # Fetch user from MongoDB
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if message.from_user.username != user.get('username'):
                update_fields['username'] = message.from_user.username
            if message.from_user.first_name != user.get('first_name'):
                update_fields['first_name'] = message.from_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        else:
            await user_collection.insert_one({
                'id': user_id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        await react_to_message(chat_id, message.id)

        # Fetch user again to update balance
        user = await user_collection.find_one({'id': user_id})
        if user:
            current_balance = user.get('balance', 0)
            new_balance = current_balance + 40
            await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})
            
            await message.reply_text(
                f"🎉 Congratulations! You have earned 40 coins for guessing correctly! \nYour new balance is {new_balance} coins."
            )
        else:
            await user_collection.insert_one({'id': user_id, 'balance': 40})
            
            await message.reply_text(
                "🎉 Congratulations! You have earned 40 coins for guessing correctly! \nYour new balance is 40 coins."
            )

        keyboard = [[InlineKeyboardButton("See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await message.reply_text(
            f'🌟 <b><a href="tg://user?id={user_id}">{escape(message.from_user.first_name)}</a></b>, you\'ve captured a new character! 🎊\n\n'
            f'📛 𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n'
            f'🌈 𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n'
            f'✨ 𝗥𝗔𝗥𝗜𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\n'
            f'⏱️ 𝗧𝗜𝗠𝗘 𝗧𝗔𝗞𝗘𝗡: <b>{time_taken_str}</b>',
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        message_id = last_characters[chat_id].get('message_id')
        if message_id:
            keyboard = [
                [InlineKeyboardButton("See Media Again", url=f"https://t.me/c/{str(chat_id)[4:]}/{message_id}")],
            ]
            await message.reply_text(
                '❌ Not quite right, brave guesser! Try again and unveil the mystery character! 🕵️‍♂️',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await message.reply_text('❌ Not quite right, brave guesser! Try again! 🕵️‍♂️')


HELP_NAME = "Gᴜᴇss"
HELP = """Use `/snatcg <character_name>` to guess the mystery character.

- Earn 40 coins for a correct guess.
- The first correct guess captures the character.
- If incorrect, you can try again.
- A 'See Harem' button lets you view your collected characters."""
