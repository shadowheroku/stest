from hasnainkk import OWNER_ID, SUDO, application 
from telegram import Update
from hasnainkk import *
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
import asyncio
import time

message_limits = {}  # Stores message limit per chat
locks = {}
message_counts = {}
user_cooldowns = {}
warned_users = {}
last_user = {}

DEFAULT_LIMIT = 100  # Default threshold

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    current_time = time.time()

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        # Cooldown Check
        if user_id in user_cooldowns:
            cooldown_end = user_cooldowns[user_id]
            if current_time < cooldown_end:
                return
            else:
                del user_cooldowns[user_id]

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                if user_id not in warned_users or current_time - warned_users[user_id] >= 600:
                    cooldown_end = current_time + 600  # 10 min
                    user_cooldowns[user_id] = cooldown_end
                    warned_users[user_id] = current_time
                    await update.message.reply_text(
                        f"⚠️ Don't Spam {update.effective_user.first_name}...\n"
                        "Your Messages Will be ignored for 10 Minutes..."
                    )
                return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        # Message count update
        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

        limit = message_limits.get(chat_id, DEFAULT_LIMIT)  # Get chat-specific limit

        if message_counts[chat_id] % limit == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0

        await guessz(update, context)

async def now_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != 6346273488:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /now {char|character}")
        return
    
    game_type = context.args[0].lower()
    
    if game_type in ['char', 'character']:
        await send_image(update, context)

async def settime_command(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    if user_id not in SUDO and user_id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /settime <1-9999999>")
        return

    limit = int(context.args[0])
    if limit < 1 or limit > 9999999:
        await update.message.reply_text("Please choose a value between 1 and 9999999.")
        return

    message_limits[chat_id] = limit  # Only for this chat
    await update.message.reply_text(f"✅ Message limit for this chat set to {limit}.")

async def changetime_command(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    if not user.id in SUDO and not user.id == OWNER_ID:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        if not chat_member.status in ["administrator", "creator"]:
            await update.message.reply_text("❌ You must be an admin to change the time limit.")
            return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /changetime 102")
        return

    limit = int(context.args[0])
    if limit < 100:
        await update.message.reply_text("Minimum limit should be 100 messages.")
        return

    message_limits[chat_id] = limit
    await update.message.reply_text(f"✅ Message limit for this chat set to {limit}.")

application.add_handler(CommandHandler("now", now_command))
application.add_handler(CommandHandler("settime", settime_command))
application.add_handler(CommandHandler("changetime", changetime_command))
application.add_handler(MessageHandler(filters.ALL, message_counter))
