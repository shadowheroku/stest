from hasnainkk import *
import random
import asyncio
from telegram import Update
from telegram.ext import CallbackContext

async def expire_session(chat_id, context, message_id):
    asyncio.current_task().set_name(f"expire_session_{chat_id}")
    await asyncio.sleep(300)  # Wait 5 minutes before notifying the user
    
    if chat_id in last_characters and 'name' in last_characters[chat_id]:
        character = last_characters[chat_id]
        keyboard = [
            [InlineKeyboardButton("See Media Again", url=f"https://t.me/c/{str(chat_id)[4:]}/{message_id}")]
        ]
        
        # Check if the character has a video URL
        if 'vid_url' in character:
            # Send the character's video and capture the sent message
            sent_message = await context.bot.send_video(
                chat_id=chat_id,
                video=character['vid_url'],
                caption=f"""❌ YOU ARE TOO SLOW! THE CHARACTER RANAWAY! 🏃‍♀️

🙃 ɴᴀᴍᴇ: {character['name']}
🏝️ ᴀɴɪᴍᴇ: {character['anime']}
🎐 ʀᴀʀɪᴛʏ: {character['rarity']}
🆔 ɪᴅ: {character['id']}""",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Send the character's image and capture the sent message
            sent_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=character['img_url'],
                caption=f"""❌ YOU ARE TOO SLOW! THE CHARACTER RANAWAY! 🏃‍♀️

🙃 ɴᴀᴍᴇ: {character['name']}
🏝️ ᴀɴɪᴍᴇ: {character['anime']}
🎐 ʀᴀʀɪᴛʏ: {character['rarity']}
🆔 ɪᴅ: {character['id']}""",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        last_characters[chat_id]['ranaway'] = True

        # Wait for 3 minutes before deleting the sent message
        await asyncio.sleep(180)  # 3 minutes
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")
