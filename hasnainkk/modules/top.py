

import logging
import os
import asyncio
from datetime import datetime
import pytz
from pymongo import MongoClient
from html import escape
from pyrogram import Client, filters
from hasnainkk import ZYRO as app, user_collection

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log", mode='a')]
)

# MongoDB Configuration
MONGO_URI = "mongodb+srv://hasnainkk:hasnainkk@cluster0.mmvls.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME = "Character_catcher"
COLLECTION_NAME = "user_collection_lmaoooo"
mongo_client = MongoClient(MONGO_URI)

# Ensure the static directory exists
os.makedirs('static', exist_ok=True)

async def fetch_leaderboard():
    db = mongo_client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    users = await collection.find().to_list(length=None)
    leaderboard = sorted(
        [
            {
                "username": user.get("username", "Unknown"),
                "first_name": user.get("first_name", "Unknown"),
                "score": len(user.get("characters", []))
            }
            for user in users
        ],
        key=lambda x: x["score"],
        reverse=True,
    )
    return leaderboard[:10]

async def generate_leaderboard_image():
    leaderboard_data = await fetch_leaderboard()
    if not leaderboard_data:
        logging.warning("No leaderboard data available.")
        return None

    local_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    
    leaderboard_items = "".join(
        f"""
        <div class='leaderboard-item'>
            <div class='user-name'>{idx + 1}. {escape(user['first_name'][:15] + '...' if len(user['first_name']) > 15 else user['first_name'])}</div>
            <div class='progress-bar-container'>
                <div class='progress-bar' style='width: {int((user['score'] / max(2000, max([u['score'] for u in leaderboard_data] or [1]))) * 100)}%;'></div>
            </div>
            <div class='user-score'>Score: {user['score']}</div>
        </div>
        """
        for idx, user in enumerate(leaderboard_data)
    )
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Leaderboard</title>
        <style>
            body {{ background-color: #2a0101; color: #fff; text-align: center; font-family: Arial; }}
            .leaderboard {{ width: 600px; background: #3e0a0a; border-radius: 15px; padding: 20px; margin: auto; }}
            .leaderboard-header {{ font-size: 2rem; font-weight: bold; }}
            .leaderboard-item {{ display: flex; align-items: center; margin-bottom: 10px; }}
            .progress-bar-container {{ flex: 1; background: #4a1414; border-radius: 20px; height: 15px; }}
            .progress-bar {{ height: 100%; background: #ff5e57; }}
            .user-score {{ min-width: 50px; text-align: right; }}
        </style>
    </head>
    <body>
        <div class='leaderboard'>
            <div class='leaderboard-header'>LEADERBOARD</div>
            {leaderboard_items}
            <div class='footer'>{local_time}</div>
        </div>
    </body>
    </html>
    """
    
    image_path = os.path.join('static', 'leaderboard.png')
    try:
        import imgkit
        options = {'format': 'png', 'width': 670, 'height': 490}
        imgkit.from_string(html_content, image_path, options=options)
        logging.info(f"Leaderboard image generated: {image_path}")
        return image_path
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        return None

@app.on_message(filters.command("top"))
async def top(_, message):
    try:
        logging.info("Fetching leaderboard...")
        image_path = await generate_leaderboard_image()

        if image_path:
            users = await user_collection.find().to_list(length=None)
            logging.info(f"Fetched {len(users)} users from the database.")

            top_users = sorted(
                users,
                key=lambda user: len(user.get('characters', [])) if isinstance(user.get('characters'), list) else 0,
                reverse=True
            )[:10]

            if top_users:
                message_text = "<b>Top 10 Users by Number of Characters:</b>\n\n"
                for idx, user in enumerate(top_users, start=1):
                    character_count = len(user.get('characters', [])) if isinstance(user.get('characters'), list) else 0
                    first_name = user.get('first_name', 'Unknown')
                    user_id = user.get('id')
                    user_link = f'<a href="tg://openmessage?user_id={user_id}">{first_name}</a>' if user_id else first_name
                    message_text += f"{idx}. {user_link}: {character_count}\n"

                logging.info("Leaderboard message prepared.")
                await message.reply_photo(image_path, caption=message_text, parse_mode='html')
            else:
                logging.info("No users found.")
                await message.reply_text("No users found.")
        else:
            logging.error("Failed to generate leaderboard image.")
            await message.reply_text("Failed to generate the leaderboard image.")
    except Exception as e:
        logging.error(f"Error in /top command: {e}")
        await message.reply_text("An error occurred while fetching the leaderboard.")

logging.info("Leaderboard Bot is running...")
