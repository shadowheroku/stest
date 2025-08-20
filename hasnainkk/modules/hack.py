from hasnainkk import app, db as mongodb, LOGGER, user_collection
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType

# MongoDB Collections
added_name_collection = mongodb.added_name_collection
list_chat_col = mongodb.list_chat_col

# Owner ID
OWNER_ID = 6346273488


# Import last_characters
from hasnainkk.modules.guess import last_characters

# --------- MONGO FUNCTIONS ---------

async def add_name_chat(chat_id: int):
    await added_name_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}}, 
        upsert=True
    )

async def remove_name_chat(chat_id: int):
    await added_name_collection.delete_one({"chat_id": chat_id})

async def get_all_name_chats():
    chats = await added_name_collection.find().to_list(length=0)
    return [chat["chat_id"] for chat in chats]

async def is_namechat_approved(chat_id: int):
    return await added_name_collection.find_one({"chat_id": chat_id}) is not None

async def get_user_balance(user_id: int):
    user_data = await user_collection.find_one({'id': user_id})
    return user_data.get('balance', 0) if user_data else 0

async def deduct_coins(user_id: int, amount: int):
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': -amount}}
    )

# --------- COMMAND HANDLERS ---------

@app.on_message(filters.command("addnamechat") & filters.user(OWNER_ID))
async def add_name_approved(client: Client, message: Message):
    if message.chat.type != ChatType.SUPERGROUP:
        return await message.reply("❌ This command can only be used in supergroups.")
    
    await add_name_chat(message.chat.id)
    await list_chat_col.insert_one({"chat_id": message.chat.id, "status": "approved"})
    await message.reply("✅ This chat has been approved for `/name` command.")

@app.on_message(filters.command("delnamechat") & filters.user(OWNER_ID))
async def del_name_approved(client: Client, message: Message):
    if message.chat.type != ChatType.SUPERGROUP:
        return await message.reply("❌ This command can only be used in supergroups.")
    
    await remove_name_chat(message.chat.id)
    await list_chat_col.delete_one({"chat_id": message.chat.id})
    await message.reply("❌ This chat has been removed from `/name` command access.")

@app.on_message(filters.command("chatnamelist") & filters.user(OWNER_ID))
async def list_name_chats(client: Client, message: Message):
    chats = await list_chat_col.find().to_list(length=0)
    if not chats:
        await message.reply("❌ No approved chats found.")
        return
    text = "**Approved Chats for `/name`:**\n\n" + "\n".join([f"`{c['chat_id']}`" for c in chats])
    await message.reply(text)

# --------- /name COMMAND ---------

@app.on_message(filters.command("name") & filters.group)
async def send_character_info(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_namechat_approved(chat_id):
        return await message.reply("❌ This group is not allowed to use `/name` command.")

    if chat_id not in last_characters or 'name' not in last_characters[chat_id]:
        await message.reply("⚠️ No character session found in this group.")
        return

    # Check if user is not owner
    if user_id != OWNER_ID:
        # Get user's balance
        user_balance = await get_user_balance(user_id)
        required_coins = 2000
        
        if user_balance < required_coins:
            return await message.reply(f"❌ You need {required_coins} coins to use this command. Your balance: {user_balance} coins")
        
        # Deduct coins
        await deduct_coins(user_id, required_coins)
        new_balance = await get_user_balance(user_id)
        await message.reply(f"ℹ️ 2000 coins deducted for using /name command. New balance: {new_balance} coins")

    character = last_characters[chat_id]
    character_id = character.get("id", "Unknown")
    character_name = character.get("name", "Unknown")
    anime_name = character.get("anime", "Unknown")
    image_url = character.get("img_url", "")

    caption = (
        f"📌 **Character Info**\n\n"
        f"🆔 ID: `{character_id}`\n"
        f"👤 Name: `{character_name}`\n"
        f"🎞️ Anime: `{anime_name}`\n"
        f"🔗 Handle to Steal: `/snatch {character_name}`"
    )

    try:
        await client.send_photo(
            chat_id=user_id,
            photo=image_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )
        await message.reply("✅ Character info sent to your DM.")
    except Exception as e:
        LOGGER.error(f"Error sending character info: {e}")
        await message.reply("⚠️ Failed to send character info. Please start the bot in DM first.")
