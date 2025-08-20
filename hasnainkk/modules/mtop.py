import logging
import os
import subprocess
from datetime import datetime
import pytz
from pymongo import MongoClient
from html import escape
from urllib.parse import quote_plus
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from hasnainkk import application, user_collection
import asyncio
import html

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", mode='a')
    ]
)

# MongoDB configuration
MONGO_URI = "mongodb+srv://hasnainkk:hasnainkk@cluster0.mmvls.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME = "gaming_create"
COLLECTION_NAME = "gamimg_user_collection"
mongo_client = MongoClient(MONGO_URI)

# Ensure the static directory exists
if not os.path.exists('static'):
    os.makedirs('static')

# Helper function to fetch leaderboard data based on balance
def fetch_balance_leaderboard():
    db = mongo_client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    users = collection.find({})
    leaderboard = sorted(
        [
            {
                "username": user.get("username", "Unknown"),
                "first_name": user.get("first_name", "Unknown"),
                "balance": user.get("balance", 0)
            }
            for user in users
        ],
        key=lambda x: x["balance"],
        reverse=True,
    )
    return leaderboard[:10]

def generate_balance_leaderboard_image():
    leaderboard_data = fetch_balance_leaderboard()

    if not leaderboard_data:
        logging.warning("No leaderboard data available.")
        return None

    local_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")

    # Create HTML content for the leaderboard
    leaderboard_items = ""
    for idx, user in enumerate(leaderboard_data, start=1):
        name = escape(user['first_name'][:15] + '...' if len(user['first_name']) > 15 else user['first_name'])
        balance = user['balance']
        progress_width = int((balance / max(2000, max([u['balance'] for u in leaderboard_data] or [1]))) * 100)

        leaderboard_items += f"""
        <div class="leaderboard-item">
            <div class="user-name">{idx}. {name}</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {progress_width}%;"></div>
            </div>
            <div class="user-balance">Balance: {balance}</div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Leaderboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #2a0101;
                color: #fff;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .leaderboard {{
                width: 600px;
                background: #3e0a0a;
                border-radius: 15px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.8);
                padding: 20px;
            }}
            .leaderboard-header {{
                font-size: 2rem;
                font-weight: bold;
                text-align: center;
                margin-bottom: 20px;
                border-bottom: 2px solid #b71c1c;
                padding-bottom: 10px;
            }}
            .leaderboard-item {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            .user-name {{
                width: 150px;
                font-weight: bold;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .progress-bar-container {{
                flex: 1;
                background: #4a1414;
                border-radius: 20px;
                overflow: hidden;
                margin: 0 15px;
                height: 15px;
                position: relative;
            }}
            .progress-bar {{
                height: 100%;
                background: #ff5e57;
                transition: width 0.3s ease-in-out;
            }}
            .user-balance {{
                min-width: 80px;
                text-align: right;
            }}
            .footer {{
                text-align: center;
                margin-top: 15px;
                font-size: 0.8rem;
                color: #ccc;
            }}
        </style>
    </head>
    <body>
        <div class="leaderboard">
            <div class="leaderboard-header">BALANCE LEADERBOARD</div>
            {leaderboard_items}
            <div class="footer">{local_time}</div>
        </div>
    </body>
    </html>
    """

    image_path = os.path.join('static', 'balance_leaderboard.png')

    # Cleanup previous image if it exists
    if os.path.exists(image_path):
        os.remove(image_path)

    try:
        # Use imgkit to generate an image from the HTML
        import imgkit
        options = {
            'format': 'png',
            'width': 670,
            'height': 490,
        }
        imgkit.from_string(html_content, image_path, options=options)

        logging.info(f"Image generated successfully: {image_path}")
        return image_path
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        return None

# Command to display the balance leaderboard
async def balance_top(update: Update, context: CallbackContext):
    top_users = await user_collection.find(
        {}, 
        projection={'id': 1, 'first_name': 1, 'last_name': 1, 'balance': 1}
    ).sort('balance', -1).limit(10).to_list(10)

    # Create a message with the top users
    top_users_message = "Top 10 Users with Highest Balance:\n"
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        last_name = user.get('last_name', '')
        user_id = user.get('id', 'Unknown')

        # Concatenate first_name and last_name if last_name is available
        full_name = f"{first_name} {last_name}" if last_name else first_name

        # Escape full_name to ensure it's safe for HTML
        full_name = html.escape(full_name)

        top_users_message += (
            f"{i}. <a href='tg://user?id={user_id}'>{full_name}</a>, \n"
            f"Balance: 💵{user.get('balance', 0)} coins\n\n"
        )

    try:
        logging.info("Fetching balance leaderboard...")
        loop = asyncio.get_running_loop()
        image_path = await loop.run_in_executor(None, generate_balance_leaderboard_image)

        if image_path:
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(photo=img, caption=top_users_message, parse_mode='HTML')
        else:
            logging.error("Failed to generate balance leaderboard image.")
            await update.message.reply_text("Failed to generate the balance leaderboard image.")
    except Exception as e:
        logging.error(f"Error in /balance_top command: {e}")
        await update.message.reply_text("An error occurred while fetching the balance leaderboard.")

# Define the command handler for /balance_top
balance_top_handler = CommandHandler(
    ['mtop', 'moneytop', 'cointop', 'balancetop'],  # List of command aliases
    balance_top
)

# Add the handler to the application
application.add_handler(balance_top_handler)
