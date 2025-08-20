from pyrogram import Client, filters, enums  
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import time
import html
from hasnainkk import app, PHOTO_URL as PHOTO_URLS
from hasnainkk import user_collection, top_global_groups_collection

# Simple in-memory cache for 30 seconds
cache = {
    "top_users": {"data": None, "time": 0},
    "top_groups": {"data": None, "time": 0},
    "top_coins": {"data": None, "time": 0},
    "top_stars": {"data": None, "time": 0},
}
CACHE_DURATION = 30  # seconds

async def get_top_users():
    now = time.time()
    if cache["top_users"]["data"] and (now - cache["top_users"]["time"] < CACHE_DURATION):
        return cache["top_users"]["data"]
    pipeline = [
        {
            "$project": {
                "id": 1,
                "first_name": 1,
                "characters_count": { "$size": {"$ifNull": ["$characters", []]} }
            }
        },
        {
            "$sort": { "characters_count": -1 }
        },
        {
            "$limit": 10
        }
    ]
    cursor = user_collection.aggregate(pipeline)
    data = await cursor.to_list(length=10)
    cache["top_users"] = {"data": data, "time": now}
    return data

async def get_top_groups():
    now = time.time()
    if cache["top_groups"]["data"] and (now - cache["top_groups"]["time"] < CACHE_DURATION):
        return cache["top_groups"]["data"]
    cursor = top_global_groups_collection.aggregate([
        {"$match": {"count": {"$gt": 0}}},
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    data = await cursor.to_list(length=10)
    cache["top_groups"] = {"data": data, "time": now}
    return data

async def get_top_coin_users():
    now = time.time()
    if cache["top_coins"]["data"] and (now - cache["top_coins"]["time"] < CACHE_DURATION):
        return cache["top_coins"]["data"]
    data = await user_collection.find().sort("balance", -1).limit(10).to_list(length=10)
    cache["top_coins"] = {"data": data, "time": now}
    return data

async def get_top_star_users():
    now = time.time()
    if cache["top_stars"]["data"] and (now - cache["top_stars"]["time"] < CACHE_DURATION):
        return cache["top_stars"]["data"]
    data = await user_collection.find().sort("golden_stars", -1).limit(10).to_list(length=10)
    cache["top_stars"] = {"data": data, "time": now}
    return data

async def generate_leaderboard(data, title, is_user=True):
    message = f"<b>🏆 {title} 🏆</b>\n\n"
    for i, item in enumerate(data, start=1):
        if is_user:
            user_id = item.get('id', 'Unknown')
            name = html.escape(item.get('first_name', 'Unknown'))
            if len(name) > 15:
                name = name[:15] + '...'
            if title == "CHARACTER LEADERBOARD":
                count = item.get('characters_count', len(item.get('characters', [])))
            elif title == "COIN LEADERBOARD":
                count = item.get('balance', 0)
            elif title == "STAR LEADERBOARD" or title == "GOLDEN STARS LEADERBOARD":
                count = item.get('golden_stars', 0)
            else:
                count = 0
            message += f"{i}. <a href='tg://user?id={user_id}'><b>{name}</b></a> ➾ <b>{count}</b>\n"
        else:
            name = html.escape(item.get('group_name', 'Unknown'))
            if len(name) > 20:
                name = name[:20] + '...'
            count = item.get('count', 0)
            message += f"{i}. <b>{name}</b> ➾ <b>{count}</b>\n"
    return message

# Store last message states to avoid duplicate edits
last_messages = {}

async def safe_edit_message(callback_query, new_caption, new_markup):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id
    key = f"{chat_id}_{message_id}"
    
    last_caption, last_markup = last_messages.get(key, (None, None))
    
    if new_caption != last_caption or new_markup != last_markup:
        try:
            await callback_query.edit_message_caption(
                caption=new_caption,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=new_markup
            )
            last_messages[key] = (new_caption, new_markup)
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                await callback_query.message.edit_text(f"❌ Error: {str(e)}")
    else:
        await callback_query.answer("Already showing this leaderboard!")

@app.on_message(filters.command("rank"))
async def rank_command(client, message):
    try:
        loading_msg = await message.reply("📊 Generating leaderboard...")
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ User Top", callback_data="user_top"),
             InlineKeyboardButton("Group Top", callback_data="group_top")],
            [InlineKeyboardButton("Coin Top", callback_data="coin_top"),
             InlineKeyboardButton("Star Top", callback_data="star_top")]
        ])
        
        top_users = await get_top_users()
        leaderboard = await generate_leaderboard(top_users, "CHARACTER LEADERBOARD")
        
        await loading_msg.delete()
        sent_msg = await message.reply_photo(
            photo=random.choice(PHOTO_URLS),
            caption=leaderboard,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )
        
        key = f"{sent_msg.chat.id}_{sent_msg.id}"
        last_messages[key] = (leaderboard, buttons)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_callback_query(filters.regex("^user_top$"))
async def user_top_callback(client, callback_query):
    await callback_query.answer()
    try:
        top_users = await get_top_users()
        leaderboard = await generate_leaderboard(top_users, "CHARACTER LEADERBOARD")
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ User Top", callback_data="user_top"),
             InlineKeyboardButton("Group Top", callback_data="group_top")],
            [InlineKeyboardButton("Coin Top", callback_data="coin_top"),
             InlineKeyboardButton("Star Top", callback_data="star_top")]
        ])
        
        await safe_edit_message(callback_query, leaderboard, buttons)
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")

@app.on_callback_query(filters.regex("^group_top$"))
async def group_top_callback(client, callback_query):
    await callback_query.answer()
    try:
        top_groups = await get_top_groups()
        leaderboard = await generate_leaderboard(top_groups, "GROUP LEADERBOARD", is_user=False)
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("User Top", callback_data="user_top"),
             InlineKeyboardButton("✅ Group Top", callback_data="group_top")],
            [InlineKeyboardButton("Coin Top", callback_data="coin_top"),
             InlineKeyboardButton("Star Top", callback_data="star_top")]
        ])
        
        await safe_edit_message(callback_query, leaderboard, buttons)
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")

@app.on_callback_query(filters.regex("^coin_top$"))
async def coin_top_callback(client, callback_query):
    await callback_query.answer()
    try:
        top_users = await get_top_coin_users()
        leaderboard = await generate_leaderboard(top_users, "COIN LEADERBOARD")
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("User Top", callback_data="user_top"),
             InlineKeyboardButton("Group Top", callback_data="group_top")],
            [InlineKeyboardButton("✅ Coin Top", callback_data="coin_top"),
             InlineKeyboardButton("Star Top", callback_data="star_top")]
        ])
        
        await safe_edit_message(callback_query, leaderboard, buttons)
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")

@app.on_callback_query(filters.regex("^star_top$"))
async def star_top_callback(client, callback_query):
    await callback_query.answer()
    try:
        top_users = await get_top_star_users()
        leaderboard = await generate_leaderboard(top_users, "STAR LEADERBOARD")
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("User Top", callback_data="user_top"),
             InlineKeyboardButton("Group Top", callback_data="group_top")],
            [InlineKeyboardButton("Coin Top", callback_data="coin_top"),
             InlineKeyboardButton("✅ Star Top", callback_data="star_top")]
        ])
        
        await safe_edit_message(callback_query, leaderboard, buttons)
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")
