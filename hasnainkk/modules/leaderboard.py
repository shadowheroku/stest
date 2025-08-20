import os
import random
import html

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from hasnainkk import (
    application, PHOTO_URL, OWNER_ID,
    user_collection, top_global_groups_collection,
    group_user_totals_collection
)

from hasnainkk import sudo_users as SUDO_USERS


async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in {OWNER_ID, *SUDO_USERS}:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>TOP 10 GROUPS WHO GUESSED MOST CHARACTERS</b>\n\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 15:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'
    
    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def ctop(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in {OWNER_ID, *SUDO_USERS}:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>TOP 10 USERS WHO GUESSED CHARACTERS MOST TIME IN THIS GROUP..</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 15:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'
    
    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def stat(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in {OWNER_ID, *SUDO_USERS}:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.estimated_document_count()
    group_count = len(await group_user_totals_collection.distinct('group_id'))

    await update.message.reply_text(f'Total Users: {user_count}\nTotal Groups: {group_count}')


async def send_users_document(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in {OWNER_ID, *SUDO_USERS}:
        await update.message.reply_text("Only for Sudo users...")
        return

    cursor = user_collection.find({})
    users = [doc async for doc in cursor]
    
    user_list = "\n".join([user.get('first_name', 'Unknown') for user in users])

    with open('users.txt', 'w') as f:
        f.write(user_list)

    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('users.txt')


async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in {OWNER_ID, *SUDO_USERS}:
        await update.message.reply_text("Only for Sudo users...")
        return

    cursor = top_global_groups_collection.find({})
    groups = [doc async for doc in cursor]
    
    group_list = "\n".join([group.get('group_name', 'Unknown') for group in groups])

    with open('groups.txt', 'w') as f:
        f.write(group_list)

    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('groups.txt')


# Registering Handlers
application.add_handler(CommandHandler('ctop', ctop))
application.add_handler(CommandHandler('TopGroups', global_leaderboard))
application.add_handler(CommandHandler('stat', stat))
application.add_handler(CommandHandler('list', send_users_document))
application.add_handler(CommandHandler('groups', send_groups_document))
