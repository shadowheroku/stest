from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from hasnainkk import ZYRO as app, collection, user_collection

OWNER_IDS = [6138142369, 6346273488,6346273488 ]  # Authorized owners

@app.on_message(filters.command("reqchar"), group=9197181818)
async def reqchar_command(_, message: Message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("❌ Usage: /reqchar <character_id>")

    character_id = args[1]
    character = await collection.find_one({'id': character_id})

    if not character:
        return await message.reply(f"❌ Character with ID {character_id} not found.")

    # Check if the character has a video, otherwise fallback to image
    if 'vid_url' in character:
        media_type = "video"
        media_url = character['vid_url']
    else:
        media_type = "photo"
        media_url = character['img_url']

    character_info = (
        f"📛 𝗡𝗔𝗠𝗘: <b>{character['name']}</b>\n"
        f"🌈 𝗔𝗡𝗜𝗠𝗘: <b>{character['anime']}</b>\n"
        f"✨ 𝗥𝗔𝗥𝗜𝗧𝗬: <b>{character['rarity']}</b>\n"
        f"🆔 𝗜𝗗: <b>{character['id']}</b>\n"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"approve_{character_id}_{message.from_user.id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{character_id}_{message.from_user.id}")
        ]
    ])

    caption = (
        f"REQUEST SENT TO @WomensHelpLine and @Endx0\n\n"
        f"Use the buttons below to confirm or cancel the request.\n\n"
        f"{character_info}"
    )

    if media_type == "video":
        await app.send_video(
            chat_id="@Midexoz_Support",
            video=media_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await app.send_photo(
            chat_id="@the_league_of_snatchers",
            photo=media_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )

    await message.reply("✅ Your character request has been sent to the owners. Await their response.")

@app.on_callback_query(filters.regex(r"^(approve|cancel)_(\d+)_(\d+)$"))
async def handle_approval_or_cancel(_, callback_query):
    action, character_id, user_id = callback_query.data.split('_')

    # Ensure the user is an authorized owner
    if int(callback_query.from_user.id) not in OWNER_IDS:
        return await callback_query.answer("❌ You are not authorized to approve or cancel requests.")

    # Fetch character from the database
    character = await collection.find_one({'id': character_id})
    user = await app.get_users(user_id)

    if not character:
        return await callback_query.answer("❌ Character not found.")

    if action == "approve":
        # If approved, give the character to the user
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
        await callback_query.answer(f"✅ Character {character['name']} has been given to {user.first_name}.")
        await callback_query.message.edit_text(f"✅ Approved! {character['name']} has been given to {user.first_name}.")

    elif action == "cancel":
        await callback_query.answer(f"❌ The request for {character['name']} has been cancelled.")
        await callback_query.message.edit_text(f"❌ Cancelled! The request for {character['name']} was denied.")
    
    # Remove buttons after response
    await callback_query.message.edit_reply_markup(reply_markup=None)
