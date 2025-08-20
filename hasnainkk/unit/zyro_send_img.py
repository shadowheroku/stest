

RARITY_WEIGHTS = {
    "⚪️ Common": 40,          # Most frequent
    "🟢 Medium": 20,          # Less frequent than Common
    "🟣 Rare": 12,            # Rare but obtainable
    "🟡 Legendary": 8,        # Very rare
    "💮 Special Edition": 6,  # Extremely rare
    "🔮 Limited Edition": 4,  # Ultra-rare
    "🎐 Celestial": 2.9,        # Legendary and mythical
    "💖 Valentine": 2,        # Special Valentine's rarity
    "🎃 Halloween": 2,        # Halloween themed rarity
    "❄️ Winter": 1.5,         # Winter themed rarity
    "🌧 Rainy": 1,            # Rainy season rarity
    "💸 Expensive": 0.5,      # Expensive rarity
    "👑 V. I. P.": 0.5,        # VIP rarity
    "💌 AMV": 0.1,
}

from hasnainkk import *
import random
import asyncio
from telegram import Update
from telegram.ext import CallbackContext
from hasnainkk.modules.expired import expire_session

async def delete_message(chat_id, message_id, context):
    await asyncio.sleep(300)  # 5 minutes (300 seconds)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")


async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    all_characters = list(await collection.find({}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    if chat_id in last_characters and last_characters[chat_id].get('ranaway', False):
        del last_characters[chat_id]

    if 'available_characters' not in context.user_data:
        context.user_data['available_characters'] = [
            c for c in all_characters 
            if 'id' in c 
            and c['id'] not in sent_characters.get(chat_id, [])
            and c.get('rarity') is not None 
            and c.get('rarity') != '💸 Premium Edition'
        ]

    available_characters = context.user_data['available_characters']

    cumulative_weights = []
    cumulative_weight = 0
    for character in available_characters:
        cumulative_weight += RARITY_WEIGHTS.get(character.get('rarity'), 1)
        cumulative_weights.append(cumulative_weight)

    rand = random.uniform(0, cumulative_weight)
    selected_character = None
    for i, character in enumerate(available_characters):
        if rand <= cumulative_weights[i]:
            selected_character = character
            break

    if not selected_character:
        selected_character = random.choice(all_characters)

    sent_characters[chat_id].append(selected_character['id'])
    last_characters[chat_id] = selected_character

    last_characters[chat_id]['timestamp'] = time.time()
    
    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    # Check if the character has a video URL
    if 'vid_url' in selected_character:
        sent_message = await context.bot.send_video(
            chat_id=chat_id,
            video=selected_character['vid_url'],
            caption=f"""✨ A {selected_character['rarity']} Character Appears! ✨
🔍 Use /snatch to claim this mysterious character!
💫 Hurry, before someone else snatches them!""",
            parse_mode='Markdown'
        )
    else:
        sent_message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=selected_character['img_url'],
            caption=f"""✨ A {selected_character['rarity']} Character Appears! ✨
🔍 Use /snatch to claim this mysterious character!
💫 Hurry, before someone else snatches them!""",
            parse_mode='Markdown'
        )

    last_characters[chat_id]['message_id'] = sent_message.message_id

    # Schedule message deletion after 5 minutes
    asyncio.create_task(delete_message(chat_id, sent_message.message_id, context))
    asyncio.create_task(expire_session(chat_id, context, sent_message.message_id))
    
