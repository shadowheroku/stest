from pyrogram import filters, enums
from pyrogram.types import Message
from hasnainkk import ZYRO as app, collection, user_collection

OWNER_IDS = [6138142369, 6346273488,6346273488]  # Authorized owners

@app.on_message(filters.command("give") & filters.user(OWNER_IDS))
async def give_command(_, message: Message):
    # Agar reply nahi hai, toh return kar do
    if not message.reply_to_message:
        return await message.reply("❌ Please reply to a user's message to give them the character.")

    # Command arguments check karo
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("❌ Usage: /give {character_id}")

    character_id = args[1]
    user = message.reply_to_message.from_user

    # Database se character fetch karo
    character = await collection.find_one({'id': character_id})
    if not character:
        return await message.reply(f"❌ Character with ID {character_id} not found.")

    # User ke database entry ko check karo
    user_data = await user_collection.find_one({'id': user.id})
    if user_data:
        await user_collection.update_one(
            {'id': user.id},
            {'$push': {'characters': character}}
        )
    else:
        await user_collection.insert_one({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'characters': [character],
        })

    # Video ya Image ka message set karo
    if 'vid_url' in character:
        media_message = "🎥 This character has a video!"
        media_type = "video"
        media_url = character['vid_url']
    else:
        media_message = "🖼️ This character has an image."
        media_type = "photo"
        media_url = character['img_url']

    confirmation_text = (
        f"✅ Character {character['name']} (ID: {character['id']}) has been given to {user.first_name}.\n"
        f"{media_message}"
    )
    await message.reply(confirmation_text)

    user_text = (
        f"🎉 You have received a new character!\n\n"
        f"📛 𝗡𝗔𝗠𝗘: <b>{character['name']}</b>\n"
        f"🌈 𝗔𝗡𝗜𝗠𝗘: <b>{character['anime']}</b>\n"
        f"✨ 𝗥𝗔𝗥𝗜𝗧𝗬: <b>{character['rarity']}</b>\n"
        f"🆔 𝗜𝗗: <b>{character['id']}</b>\n\n"
        f"{media_message}"
    )

    # User ko media bhejo
    if media_type == "video":
        await app.send_video(
            chat_id=user.id,
            video=media_url,
            caption=user_text,
            parse_mode=enums.ParseMode.HTML
           # parse_mode="HTML"  # Fixed the parse mode here
        )
    else:
        await app.send_photo(
            chat_id=user.id,
            photo=media_url,
            caption=user_text,
            parse_mode=enums.ParseMode.HTML
          #  parse_mode="HTML"  # Fixed the parse mode here
    )



from pyrogram import filters
from pyrogram.types import Message
from hasnainkk import ZYRO as app, collection, user_collection

OWNER_IDS = [6138142369, 6346273488, 6346273488]  # Authorized owners

@app.on_message(filters.command("giveall") & filters.user(OWNER_IDS))
async def give_all_command(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("❌ Please reply to a user's message to give them all characters.")
    
    user = message.reply_to_message.from_user
    characters = [char async for char in collection.find({})]  # Fetch all characters asynchronously
    
    if not characters:
        return await message.reply("❌ No characters found in the database.")
    
    user_data = await user_collection.find_one({'id': user.id})
    if user_data:
        await user_collection.update_one(
            {'id': user.id},
            {'$push': {'characters': {'$each': characters}}}
        )
    else:
        await user_collection.insert_one({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'characters': characters,
        })
    
    await message.reply(f"✅ All {len(characters)} characters have been given to {user.first_name}.")
        
