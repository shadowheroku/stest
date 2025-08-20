import asyncio
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from hasnainkk import ZYRO as bot
from hasnainkk import user_collection, collection

chat = "-1002277330421"

# Helper function to format time
async def format_time_delta(delta):
    try:
        seconds = delta.total_seconds()
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    except Exception as e:
        print(f"Error formatting time delta: {e}")
        return "unknown time"

# Fetch unique characters function
async def get_unique_characters(user_id):
    try:
        user_data = await user_collection.find_one({'id': user_id}, {'characters.id': 1})
        claimed_ids = [char['id'] for char in user_data.get('characters', [])] if user_data else []

        pipeline = [
            {'$match': {'id': {'$nin': claimed_ids}}},
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters if characters else []
    except Exception as e:
        print(f"Error retrieving unique characters: {e}")
        return []

# Command handler for daily claim (hclaim)
@bot.on_message(filters.command(["hclaim", "claim"]))
async def hclaim(_, message: t.Message):
    try:
        user_id = message.from_user.id
        mention = message.from_user.mention

        if str(message.chat.id) != chat:
            join_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Here", url="https://t.me/the_snatchers")]
            ])
            sent_msg = await message.reply_text(
                "🔔 ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴄʜᴀʀᴀᴄᴛᴇʀ",
                reply_markup=join_button
            )
            await asyncio.sleep(180)  # 3 minutes wait
            await sent_msg.delete()
            return

        try:
            user_data = await user_collection.find_one({'id': user_id})
            if not user_data:
                user_data = {
                    'id': user_id,
                    'username': message.from_user.username,
                    'characters': [],
                    'last_daily_reward': None
                }
                await user_collection.insert_one(user_data)

            last_claimed_date = user_data.get('last_daily_reward')
            if last_claimed_date:
                last_claimed_date = last_claimed_date.replace(tzinfo=None)
                if last_claimed_date.date() == datetime.utcnow().date():
                    remaining_time = timedelta(days=1) - (datetime.utcnow() - last_claimed_date)
                    formatted_time = await format_time_delta(remaining_time)
                    sent_msg = await message.reply_text(f"*You've already claimed today! Next reward in:* {formatted_time}")
                    await asyncio.sleep(180)
                    await sent_msg.delete()
                    return

            unique_characters = await get_unique_characters(user_id)
            if not unique_characters:
                sent_msg = await message.reply_text("*No characters found*")
                await asyncio.sleep(180)
                await sent_msg.delete()
                return

            await user_collection.update_one(
                {'id': user_id},
                {
                    '$push': {'characters': {'$each': unique_characters}},
                    '$set': {'last_daily_reward': datetime.utcnow()}
                }
            )

            for character in unique_characters:
                sent_msg = await message.reply_photo(
                    photo=character['img_url'],
                    caption=(
                        f"✨ **Cᴏɴɢʀᴀᴛs** {mention}\n\n"
                        f"🌟 **Nᴀᴍᴇ**: `{character['name']}`  \n"
                        f"🟣 **Rᴀʀɪᴛʏ**: `{character['rarity']}`  \n"
                        f"📺 **Aɴɪᴍᴇ**: `{character['anime']}`  \n"
                        f"🆔 **Iᴅ**: `{character['id']}`  \n\n"
                        f"🌸 **Cᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ ғᴏʀ ᴀɴᴏᴛʜᴇʀ ᴄʟᴀɪᴍ!** 🌟"
                    )
                )
                await asyncio.sleep(180)  # 3 minutes wait
                await sent_msg.delete()

        except Exception as e:
            print(f"Error in daily claim logic: {e}")
            sent_msg = await message.reply_text("❌ *Something went wrong, please try again later.*")
            await asyncio.sleep(180)
            await sent_msg.delete()

    except Exception as e:
        print(f"Error in hclaim command: {e}")
        sent_msg = await message.reply_text("❌ *An unexpected error occurred.*")
        await asyncio.sleep(45)
        await sent_msg.delete()
