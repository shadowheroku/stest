from pyrogram import Client, filters
from pyrogram.types import Message
from hasnainkk import user_collection, OWNER_ID, app
import html
from hydragram import handler

sudo_users = [6138142369, 6346273488]  # Sudo users list

async def get_balance(user_id):
    user_data = await user_collection.find_one({'id': user_id}, {'balance': 1, 'black_stars': 1, 'white_stars': 1, 'golden_stars': 1})
    return user_data.get('balance', 0), user_data.get('black_stars', 0), user_data.get('white_stars', 0), user_data.get('golden_stars', 0) if user_data else (0, 0, 0, 0)

async def modify_stars(client, message, star_type, action):
    sender_id = message.from_user.id
    if sender_id not in [OWNER_ID] + sudo_users:
        await message.reply_text("You are not authorized to use this command.")
        return

    args = message.command
    if len(args) < 2:
        await message.reply_text(f"Usage: /{action}{star_type} <amount> [@username/user_id] or reply to a user.")
        return

    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply_text("Invalid amount. Please enter a positive number.")
        return

    recipient_id = None
    recipient_username = None

    if message.reply_to_message:
        recipient_id = message.reply_to_message.from_user.id
        recipient_username = message.reply_to_message.from_user.username
    elif len(args) > 2:
        try:
            recipient_id = int(args[2])
        except ValueError:
            recipient_username = args[2]
            user_data = await user_collection.find_one({'username': recipient_username}, {'id': 1})
            if user_data:
                recipient_id = user_data['id']

    if not recipient_id:
        await message.reply_text("Recipient not found. Reply to a user or provide a valid user ID/username.")
        return

    update_value = amount if action == "give" else -amount
    update_field = f"{star_type}_stars"
    await user_collection.update_one({'id': recipient_id}, {'$inc': {update_field: update_value}})

    updated_balance, updated_black_stars, updated_white_stars, updated_golden_stars = await get_balance(recipient_id)

    star_emoji = {"black": "★", "white": "☆", "golden": "🌟"}[star_type]
    star_count = {"black": updated_black_stars, "white": updated_white_stars, "golden": updated_golden_stars}[star_type]

    action_text = "gave" if action == "give" else "removed"
    await message.reply_text(f"✅ You {action_text} {amount} {star_type} stars to @{html.escape(recipient_username or str(recipient_id))}.")

    await client.send_message(
        chat_id=recipient_id,
        text=f"🎉 {message.from_user.username} {action_text} {amount} {star_type} stars! \n{star_emoji} {star_type.capitalize()} Stars: {star_count}"
    )

# Commands to give stars
#@app.on_message(filters.command("giveblackstar"), group=9999)
@handler("giveblackstar")
async def give_black_star(client: Client, message: Message):
    await modify_stars(client, message, "black", "give")

@app.on_message(filters.command("givewhitestar"), group=9999)
async def give_white_star(client: Client, message: Message):
    await modify_stars(client, message, "white", "give")

@app.on_message(filters.command("givegoldenstar"), group=9999)
async def give_golden_star(client: Client, message: Message):
    await modify_stars(client, message, "golden", "give")

# Commands to delete stars
@app.on_message(filters.command("deleteblackstar"), group=9999)
async def delete_black_star(client: Client, message: Message):
    await modify_stars(client, message, "black", "delete")

@app.on_message(filters.command("deletewhitestar"), group=9999)
async def delete_white_star(client: Client, message: Message):
    await modify_stars(client, message, "white", "delete")

@app.on_message(filters.command("deletegoldenstar"), group=9999)
async def delete_golden_star(client: Client, message: Message):
    await modify_stars(client, message, "golden", "delete")
