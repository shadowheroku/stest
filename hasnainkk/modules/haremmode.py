from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from pyrogram.enums import ParseMode  # Importing ParseMode
import aiohttp
from hasnainkk import ZYRO as app

# Initialize active_users dictionary
active_users = {}

# your_file.py
from hasnainkk import BASE_API_URL

# Fetch a specific user's collection from the external API
async def fetch_user_collection_from_api(user_id):
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_API_URL}/user-collection/{user_id}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


@app.on_message(filters.command("hmode"), group=98809191)
async def hmode(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name  # Fetch the user's name
    user_data = await fetch_user_collection_from_api(user_id)  # Fetch collection from API

    if not user_data or 'characters' not in user_data:
        await message.reply_text("Your list is empty.")
        return

    characters = user_data['characters']
    total_characters = len(characters)
    rarities = {character['rarity'] for character in characters}

    # Create buttons for rarities
    buttons = [
        [InlineKeyboardButton(rarity, callback_data=f'rarity2_{rarity}_{user_id}')]
        for rarity in rarities
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    # Send the photo with the user's name and character count
    await message.reply_photo(
        photo="https://files.catbox.moe/8fi5ta.jpg",
        caption=f"🌟 **{user_name}'s Mode** 🌟\n\n🧙 Total Characters: {total_characters}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN  # Use Markdown for rich text formatting
    )

@app.on_callback_query(filters.regex('^rarity2_'))
async def rarity2_callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    parts = data.split('_')

    if len(parts) < 3:
        await callback_query.answer("Invalid callback data.", show_alert=True)
        return

    rarity = parts[1]
    hmode_user_id = int(parts[2])

    # Ensure only the original user can interact
    if user_id != hmode_user_id:
        await callback_query.answer("This is not for you.", show_alert=True)
        return

    user_data = await fetch_user_collection_from_api(hmode_user_id)

    if not user_data or 'characters' not in user_data:
        await callback_query.answer("Your list is empty.", show_alert=True)
        return

    # Filter characters by rarity
    filtered_characters = [character for character in user_data['characters'] if character['rarity'] == rarity]

    # Paginate results (10 characters per page)
    page = 1
    chunk_size = 10
    start = (page - 1) * chunk_size
    end = start + chunk_size
    current_characters = filtered_characters[start:end]

    message = '\n'.join([
        f"🆔 ID: {char['id']}\n🎗️ Rarity: {char['rarity']}\n👁️‍🗨️ Character: {char['name']}\n\n"
        for char in current_characters
    ])

    keyboard = []
    if end < len(filtered_characters):
        keyboard.append([InlineKeyboardButton("Next", callback_data=f"next_{rarity}_{page+1}_{hmode_user_id}")])
    if start > 0:
        keyboard.append([InlineKeyboardButton("Previous", callback_data=f"prev_{rarity}_{page-1}_{hmode_user_id}")])
    keyboard.append([InlineKeyboardButton("Back", callback_data=f"back_1_{hmode_user_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await callback_query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

@app.on_callback_query(filters.regex('^back_1_'))
async def back_callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    parts = data.split('_')

    if len(parts) < 3:
        await callback_query.answer("Invalid callback data.", show_alert=True)
        return

    hmode_user_id = int(parts[2])  # Extract the user ID from callback data

    # Ensure only the original user can interact
    if user_id != hmode_user_id:
        await callback_query.answer("This is not for you.", show_alert=True)
        return

    # Fetch the user's data again
    user_data = await fetch_user_collection_from_api(hmode_user_id)

    if not user_data or 'characters' not in user_data:
        await callback_query.answer("Your list is empty.", show_alert=True)
        return

    # Extract rarities to regenerate the buttons
    rarities = {character['rarity'] for character in user_data['characters']}
    
    # Prepare the user text message with their details
    username = callback_query.from_user.first_name
    total_characters = len(user_data['characters'])
    user_message = f"🌟 **{username}'s Mode** 🌟\n\n🧙 Total Characters: {total_characters}"

    # Generate rarity buttons
    buttons = [
        [InlineKeyboardButton(rarity, callback_data=f'rarity2_{rarity}_{user_id}')]
        for rarity in rarities
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)

    # # Update the media with the photo and user details
    # await callback_query.edit_message_media(
    #     media=InputMediaPhoto("https://telegra.ph/file/036135b624b6a7d1babee.jpg"),
    #     reply_markup=reply_markup
    # )
    # Update the caption with user details
    await callback_query.edit_message_caption(
        caption=user_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN  # Use Markdown for formatting
    )

@app.on_callback_query(filters.regex('^(next|prev)_'))
async def pagination_callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    parts = data.split('_')

    if len(parts) < 4:
        await callback_query.answer("Invalid callback data.", show_alert=True)
        return

    action, rarity, page, hmode_user_id = parts[0], parts[1], int(parts[2]), int(parts[3])

    # Ensure only the original user can interact
    if user_id != hmode_user_id:
        await callback_query.answer("This is not for you.", show_alert=True)
        return

    user_data = await fetch_user_collection_from_api(hmode_user_id)

    if not user_data or 'characters' not in user_data:
        await callback_query.answer("Your list is empty.", show_alert=True)
        return

    # Filter characters by rarity
    filtered_characters = [character for character in user_data['characters'] if character['rarity'] == rarity]

    # Paginate results
    chunk_size = 10
    start = (page - 1) * chunk_size
    end = start + chunk_size
    current_characters = filtered_characters[start:end]

    message = '\n'.join([
        f"🆔 ID: {char['id']}\n🎗️ Rarity: {char['rarity']}\n👁️‍🗨️ Character: {char['name']}\n\n"
        for char in current_characters
    ])

    keyboard = []
    if end < len(filtered_characters):
        keyboard.append([InlineKeyboardButton("Next", callback_data=f"next_{rarity}_{page+1}_{hmode_user_id}")])
    if start > 0:
        keyboard.append([InlineKeyboardButton("Previous", callback_data=f"prev_{rarity}_{page-1}_{hmode_user_id}")])
    keyboard.append([InlineKeyboardButton("Back", callback_data=f"back_1_{hmode_user_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await callback_query.edit_message_caption(caption=message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
