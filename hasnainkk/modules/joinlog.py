from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated
from pyrogram.enums import ChatType, ChatMemberStatus
from hasnainkk.config import Config as a
from hasnainkk import ZYRO as app
#from Anonymous import app
from motor.motor_asyncio import AsyncIOMotorClient

LOG_CHANNEL_ID = "-1002685904693"

#app = Client("Uff",
#             api_id=a.api_id,
#             api_hash=a.api_hash,
#             bot_token=a.TOKEN,
#            )

# MongoDB connection setup
client = AsyncIOMotorClient("mongodb+srv://herobh123456:hasnainkk07@hasnainkk07.uqjekii.mongodb.net/?retryWrites=true&w=majority")
db = client["ufff"]
chats_collection = db["chats"]

async def add_chat(chat_id: int):
    """Add a chat ID to the database."""
    await chats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}},
        upsert=True
    )

# Event for handling new chat additio
@app.on_chat_member_updated(filters.group, group=898989898979) #@app.on_message(filters.new_chat_members) #, group=898989898979)
async def handler(client, event: ChatMemberUpdated):
    """Log new group joins to LOG_CHANNEL_ID with Pyrogram."""
    if event.new_chat_member and event.new_chat_member.user.id == (await client.get_me()).id:
        chat = await client.get_chat(event.chat.id)
        added_by = event.from_user

        # Get member count
        member_count = await client.get_chat_members_count(chat.id)

        # Get invite link if available
        try:
            invite_link = await client.export_chat_invite_link(chat.id)
        except Exception as e:
            invite_link = "Not available"

        added_by_mention = f"<a href='tg://user?id={added_by.id}'>{added_by.first_name}</a>"

        # Compose the message with Snatch Bot features
        message_text = f"""
🛡️ **Hello {added_by_mention},**
Thanks for adding me to the group [{chat.title}](https://t.me/{chat.username})! 🛡️

I'm here to add some fun and interactivity to your group with the following features:

✨ **Features**:
1. **Guess Characters**: Play character guessing games with your group.
2. **Trade Characters**: Trade characters with other members.
3. **Gift Characters**: Gift characters to fellow members.
4. **Collection**: Keep track of your own character collection.
5. **Top Users/Groups**: See who’s leading in character guesses.

🚀 **Let's make this group more fun together!**  
Need help? Just ask! 💬
"""

        # Send the message to the new group
        try:
            await client.send_message(
                chat.id,
                message_text,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Add Me", url="http://t.me/Snatch_Your_Character_Bot?startgroup=true")],
                    [InlineKeyboardButton("Updates", url="https://t.me/MidexOzBotUpdates")]
                ])
            )
        except Exception as e:
            print(f"Failed to send welcome message to the group: {e}")

        # Log the new group details in the log channel
        log_message = f"""
#NEW_GROUP
┏━━━━━━━━━━━━━━━┓
➢ 𝖦𝗋𝗈𝗎𝗉 𝖭𝖺𝗆𝖾: {chat.title}
➢ 𝖦𝗋𝗈𝗎𝗉 𝖨𝖩: {chat.id}
➢ 𝖦𝗋𝗈𝗎𝗉 𝖴𝗌𝖾𝗋𝗇𝖺𝗆𝖾: @{chat.username if chat.username else 'None'}
➢ 𝖠𝖽𝖽𝖾𝖽 𝖡𝗒: {added_by_mention} [𝖨𝖣: {added_by.id}]
➢ 𝖬𝖾𝗆𝖻𝖾𝗋 𝖢𝗈𝗎𝗇𝗍: {member_count}
➢ 𝖫𝗂𝗇𝗄: {invite_link}
┗━━━━━━━━━━━━━━━┛
"""
        try:
            await client.send_message(LOG_CHANNEL_ID, log_message)
        except Exception as e:
            print(f"Failed to send message to LOG_CHANNEL_ID: {e}")
