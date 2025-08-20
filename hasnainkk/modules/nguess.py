

import time
import random
import re
import asyncio
from html import escape
import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from hasnainkk import collection, user_collection, LOGGER, app, react_to_message
from hasnainkk import TOKEN



GROUP_ID = [-1002076327473,  -1002003248653]
COOLDOWN_PERIOD = 4 * 60 * 60  # 4 hours cooldown after 100 guesses
MAX_GUESSES = 100  # Maximum number of guesses before cooldown
GUESS_TIMEOUT = 48 * 60 * 60  # 48 hours timeout for each guess session

# Store ongoing sessions and other necessary data
ongoing_sessions = {}
user_total_guesses = {}
streak_data = {"current_streak": 0, "last_correct_user": None}

chat_filter = filters.chat(GROUP_ID)

text_filter = filters.text
command_filter = filters.create(lambda _, __, message: message.text and message.text.startswith("/"))
chat_filter = filters.chat(GROUP_ID)


@app.on_message(filters.command("nguess") & ~filters.chat(GROUP_ID))
async def redirect_to_group(client: Client, message: Message):
    """
    Redirects users to the specified group when they attempt to use the /nguess command in the wrong group.
    """
    group_link = "https://t.me/Anime_Snatchers"  # Replace with your group link
    await message.reply(
        f"⚠️ This command can only be used in our official group.\n"
        f"👉 [Click here to join the group!]({group_link})",
        disable_web_page_preview=True,
    )

async def get_random_character():
    try:
        all_characters = await collection.find({}).to_list(None)  # Fetch all characters as a list
        if not all_characters:
            LOGGER.warning("No characters found in the database.")
            return None
        return random.choice(all_characters)
    except Exception as e:
        LOGGER.error(f"Error fetching random character: {e}")
        return None

@app.on_message(filters.command("nguess") & chat_filter)
async def start_nguess(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if the user is on cooldown
    if user_id in user_total_guesses and user_total_guesses[user_id] >= MAX_GUESSES:
        await message.reply(f"🕒 You have reached the maximum guesses! Please wait {COOLDOWN_PERIOD // 60 // 60} hours before playing again.")
        return

    # Start a new session
    random_character = await get_random_character()
    if not random_character:
        await message.reply("⚠️ Error fetching character. Please try again later.")
        return

    # Initialize the new session for this chat
    ongoing_sessions[chat_id] = {
        "current_character": random_character,
        "start_time": time.time(),  # Track the start time for timeout
        "guesses": {},  # Track guesses by user
        "guessed": False  # Track if the correct guess has been made
    }

    await send_character(message, random_character)

async def send_character(message: Message, character) -> None:
    try:
        # Check if the character comes with a star (15% chance)
        star_type = None
        if random.random() < 0.15:  # 15% chance
            star_type = random.choice(["black_stars", "white_stars"])  # Randomly choose between black and white star

        # Attempt to send the character's image
        character_id = character.get("id", "Unknown ID")  # Safely get the ID or fallback
        caption = f"✨ Guess the character's name! \n\n⏳ You have 5 minutes to guess."
        if star_type:
            caption += f"\n🌟 This character comes with a {star_type.replace('_', ' ')}! Guess correctly to earn it!"

        sent_message = await message.reply_photo(
            photo=character["img_url"],
            caption=caption,
        )

        # Store the star type in the session
        chat_id = message.chat.id
        if chat_id in ongoing_sessions:
            ongoing_sessions[chat_id]["star_type"] = star_type

        await asyncio.sleep(90)
        await sent_message.delete()
    except KeyError as e:
        # Handle missing keys
        LOGGER.error(f"Missing key in character data (ID: {character.get('id', 'Unknown ID')}): {e}")
        await message.reply(f"⚠️ Character data is incomplete (ID: {character.get('id', 'Unknown ID')}). /nguess")
    except Exception as e:
        # Handle other errors
        LOGGER.error(f"Error sending image for character (ID: {character.get('id', 'Unknown ID')}): {e}")
        await message.reply(f"⚠️ Unable to send the character image (ID: {character.get('id', 'Unknown ID')}). /nguess")

async def send_next_character(message: Message) -> None:
    # Fetch the next random character
    next_character = await get_random_character()
    if next_character:
        await send_character(message, next_character)
    else:
        await message.reply("⚠️ No more characters available. Please try again later.")

@app.on_message(filters.text & ~command_filter & chat_filter)
async def handle_guess(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Ignore messages starting with '/'
    if message.text.startswith('/'):
        return

    if chat_id not in ongoing_sessions or "current_character" not in ongoing_sessions[chat_id]:
        return

    session = ongoing_sessions[chat_id]
    current_character = session["current_character"]

    if "name" not in current_character:
        LOGGER.error(f"Character data missing 'name' key: {current_character}")
        return

    guess = message.text.strip().lower()
    correct_name = current_character["name"].strip().lower()

    if re.search(r'\b' + re.escape(guess) + r'\b', correct_name) and not session["guessed"]:
        # Mark the first correct guess
        session["guessed"] = True

        # React to the message
        await react_to_message(chat_id, message.id)
        streak_data["current_streak"] += 1
        streak_data["last_correct_user"] = user_id

        # Reward the user with coins
        try:
            user = await user_collection.find_one({"id": user_id})
            if user:
                new_balance = user.get("balance", 0) + 20
                await user_collection.update_one({"id": user_id}, {"$set": {"balance": new_balance}})
            else:
                await user_collection.insert_one({"id": user_id, "balance": 20})
        except Exception as e:
            LOGGER.error(f"Error updating user balance: {e}")

        # Reward the user with a star if the character has one
        if "star_type" in session and session["star_type"]:
            star_type = session["star_type"]
            try:
                user = await user_collection.find_one({"id": user_id})
                if user:
                    new_star_count = user.get(star_type, 0) + 1
                    await user_collection.update_one({"id": user_id}, {"$set": {star_type: new_star_count}})
                else:
                    await user_collection.insert_one({"id": user_id, star_type: 1})
            except Exception as e:
                LOGGER.error(f"Error updating user star count: {e}")

            await message.reply(f"🎉 You've earned a {star_type.replace('_', ' ')}! Check your balance with /balance.")
        else:
            await message.reply(f"🎉 Correct! You've earned 20 coins!\nCurrent Streak: {streak_data['current_streak']}! 🎉")

        # Handle streak milestones
        if streak_data["current_streak"] in [50, 100]:
            reward = 1000 if streak_data["current_streak"] == 50 else 2000
            try:
                user = await user_collection.find_one({"id": streak_data["last_correct_user"]})
                if user:
                    new_balance = user.get("balance", 0) + reward
                    await user_collection.update_one({"id": streak_data["last_correct_user"]}, {"$set": {"balance": new_balance}})
                else:
                    await user_collection.insert_one({"id": streak_data["last_correct_user"], "balance": reward})
            except Exception as e:
                LOGGER.error(f"Error rewarding milestone coins: {e}")

            await message.reply(
                f"🏆 Streak {streak_data['current_streak']} achieved by [User](tg://user?id={streak_data['last_correct_user']})! 🎉\n"
                f"They've been rewarded with {reward} coins! 💰"
            )

            # Reset the streak
            streak_data["current_streak"] = 0
            streak_data["last_correct_user"] = None

        # Reset session after a correct guess
        ongoing_sessions[chat_id]["current_character"] = await get_random_character()
        ongoing_sessions[chat_id]["start_time"] = time.time()  # Reset the start time for the new character
        ongoing_sessions[chat_id]["guessed"] = False  # Reset guessed flag
        await send_character(message, ongoing_sessions[chat_id]["current_character"])

    else:
        # If no correct guess and timeout is reached, skip the current character
        if time.time() - session["start_time"] > GUESS_TIMEOUT:
            await message.reply("⏳ Time's up! Moving to the next character.")
            ongoing_sessions[chat_id]["current_character"] = await get_random_character()
            ongoing_sessions[chat_id]["start_time"] = time.time()  # Reset the start time for the new character
            await send_character(message, ongoing_sessions[chat_id]["current_character"])
