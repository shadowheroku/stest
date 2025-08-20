from hasnainkk import app, collection as character_collection, db
from pyrogram import filters, enums
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQuery,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)
import hashlib
import re
from string import ascii_uppercase

anime_token_collection = db.anime_tokens  # Stores anime-to-token mapping

# Generate a unique token for each anime
def generate_token(anime_name: str) -> str:
    return hashlib.md5(anime_name.lower().encode()).hexdigest()[:10]

# /animelist command - Shows all letters at once in 8x3 grid
@app.on_message(filters.command("animelist"))
async def anime_list_handler(client, message: Message):
    letters = list(ascii_uppercase)
    
    # Create 4 rows with 6-7 letters each
    keyboard = []
    for i in range(0, len(letters), 3):
        row = letters[i:i+3]
        keyboard.append([
            InlineKeyboardButton(letter, callback_data=f"letter_{letter}")
            for letter in row
        ])
    
    # Add close button at bottom
    keyboard.append([InlineKeyboardButton("𝗖𝗟𝗢𝗦𝗘", callback_data="close_letters")])
    
    await message.reply(
        "**Select a Letter**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Close button
@app.on_callback_query(filters.regex("^close_letters"))
async def close_letters_handler(client, callback_query: CallbackQuery):
    await callback_query.message.delete()

# When a letter is selected (e.g., "A")
@app.on_callback_query(filters.regex(r"^letter_"))
async def anime_by_letter(client, callback_query: CallbackQuery):
    letter = callback_query.data.split("_")[1]
    animes = await character_collection.distinct("anime")
    matched = sorted(set(a for a in animes if a.upper().startswith(letter)))

    if not matched:
        return await callback_query.answer("No anime found.", show_alert=True)

    page = 0
    await show_anime_page(callback_query, matched, letter, page)

# Show anime list in pages (10 per page, 1 per row)
async def show_anime_page(callback_query, matched, letter, page):
    per_page = 10  # Now showing 10 anime per page (1 per line)
    total_pages = (len(matched) + per_page - 1) // per_page
    page_items = matched[page * per_page : (page + 1) * per_page]

    keyboard = []
    for anime_name in page_items:
        keyboard.append([InlineKeyboardButton(anime_name, callback_data=f"animeclick_{anime_name}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◁", callback_data=f"nav_{letter}_{page-1}"))
    nav.append(InlineKeyboardButton("𝗕𝗔𝗖𝗞", callback_data="animelist_back"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("▷", callback_data=f"nav_{letter}_{page+1}"))
    if nav:
        keyboard.append(nav)

    await callback_query.message.edit_text(
        f"**Anime Starting with {letter}**\nPage {page + 1}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# Handle anime pagination (Next/Prev)
@app.on_callback_query(filters.regex(r"^nav_"))
async def anime_nav(client, callback_query: CallbackQuery):
    _, letter, page = callback_query.data.split("_")
    animes = await character_collection.distinct("anime")
    matched = sorted(set(a for a in animes if a.upper().startswith(letter)))
    await show_anime_page(callback_query, matched, letter, int(page))

# Back button (returns to letter selection)
@app.on_callback_query(filters.regex("^animelist_back"))
async def animelist_back_handler(client, callback_query: CallbackQuery):
    letters = list(ascii_uppercase)
    
    # Recreate the original letter grid
    keyboard = []
    for i in range(0, len(letters), 3):
        row = letters[i:i+3]
        keyboard.append([
            InlineKeyboardButton(letter, callback_data=f"letter_{letter}")
            for letter in row
        ])
    
    keyboard.append([InlineKeyboardButton("𝗖𝗟𝗢𝗦𝗘", callback_data="close_letters")])
    
    await callback_query.message.edit_text(
        "**Select a Letter**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# When an anime is selected (e.g., "Attack on Titan")
@app.on_callback_query(filters.regex("^animeclick_"))
async def anime_selected(client, callback_query: CallbackQuery):
    anime_name = callback_query.data.split("_", 1)[1]
    token = generate_token(anime_name)

    # Save token -> anime mapping in DB
    await anime_token_collection.update_one(
        {"token": token},
        {"$set": {"anime": anime_name}},
        upsert=True,
    )

    text = f"❄️ **𝖢𝗅𝗂𝖼𝗄 𝖻𝖾𝗅𝗈𝗐 𝗍𝗈 𝗌𝖾𝖾 𝖺𝗅𝗅 𝖼𝗁𝖺𝗋𝖺𝖼𝗍𝖾𝗋𝗌 𝖿𝗋𝗈𝗆 {anime_name}**"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "𝖢𝗁𝖺𝗋𝖺𝖼𝗍𝖾𝗋𝗌 𝖫𝗂𝗌𝗍", 
                    switch_inline_query_current_chat=f"waifu_list.{token}"
                )
            ],
            [
                InlineKeyboardButton(
                    "𝗕𝗔𝗖𝗞", 
                    callback_data=f"letter_{anime_name[0].upper()}"
                )
            ]
        ]
    )
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# Handle inline queries (shows only IMAGES)
@app.on_inline_query()
async def inline_query_handler(client, inline_query: InlineQuery):
    query = inline_query.query
    if query.startswith("waifu_list."):
        token = query.split("waifu_list.")[1]
        doc = await anime_token_collection.find_one({"token": token})
        
        if not doc:
            return await inline_query.answer(
                [],
                switch_pm_text="Anime not found. Try again.",
                switch_pm_parameter="start",
            )

        anime_name = doc["anime"]
        all_characters = await character_collection.find({"anime": anime_name}).to_list(None)

        results = []
        for character in all_characters:
            if "img_url" in character:
                # Generate detailed info (shown when clicked)
                caption = (
                    f"Discover this amazing character:\n\n"                   
                    f"🌸 **Name:** {character['name']}\n"
                    f"🎌 **Anime:** {character['anime']}\n"
                  #  f"⚡ **:** {character.get('gender', 'N/A')}\n"
                    f"💎 **Rarity:** {character.get('rarity', 'N/A')}\n"
                    f"🆔 **ID:** {character.get('id', 'N/A')}"
                )

                results.append(
                    InlineQueryResultPhoto(
                        id=f"img_{character['_id']}",
                        photo_url=character["img_url"],
                        thumb_url=character["img_url"],
                        title=character["name"],
                        description=f"From {anime_name}",
                        caption=caption,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                )

        await inline_query.answer(results, cache_time=0)
