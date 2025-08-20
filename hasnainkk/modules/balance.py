from pyrogram import Client, filters
from pyrogram.types import Message
from hasnainkk import user_collection, OWNER_ID, app
import html

# Function to get user's balance
async def get_balance(user_id):
    user_data = await user_collection.find_one({'id': user_id}, {'balance': 1, 'black_stars': 1, 'white_stars': 1, 'golden_stars': 1})
    return user_data.get('balance', 0), user_data.get('black_stars', 0), user_data.get('white_stars', 0), user_data.get('golden_stars', 0) if user_data else (0, 0, 0, 0)

# Balance command to show the user's balance and star count
@app.on_message(filters.command("balance"), group=998191977)
async def balance(client: Client, message: Message):
    user_id = message.from_user.id

    # Fetch the user's balance and star counts
    user_balance, user_black_stars, user_white_stars, user_golden_stars = await get_balance(user_id)

    # Format the response
    response = (
        f"{message.from_user.first_name} ◈⌠ {user_balance} coins⌡\n"
        f"★ Black Stars: {user_black_stars}\n"
        f"☆ White Stars: {user_white_stars}\n"
        f"⭐ Golden Stars: {user_golden_stars}"
    )

    # Send the response without replying to any message
    await message.reply_text(response, reply_to_message_id=False)

# Pay command to transfer coins
@app.on_message(filters.command("pay"), group=98817981)
async def pay(client: Client, message: Message):
    sender_id = message.from_user.id
    args = message.command

    if len(args) < 2:
        await message.reply_text("Usage: /pay <amount> [@username/user_id] or reply to a user.")
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

    sender_balance, _, _, _ = await get_balance(sender_id)
    if sender_balance < amount:
        await message.reply_text("Insufficient balance.")
        return

    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}})

    updated_sender_balance, _, _, _ = await get_balance(sender_id)
    updated_recipient_balance, _, _, _ = await get_balance(recipient_id)

    await message.reply_text(
        f"✅ You paid {amount} coins to @{html.escape(recipient_username or str(recipient_id))}."
        f"\n💰 Your New Balance: {updated_sender_balance} coins"
    )

    await client.send_message(
        chat_id=recipient_id,
        text=f"🎉 You received {amount} coins from @{message.from_user.username}! "
        f"\n💰 Your New Balance: {updated_recipient_balance} coins"
    )

# Command to give money (Sudo users only)
sudo_users = [6138142369, 6346273488 , 6346273488]  # Add other sudo user IDs here

@app.on_message(filters.command("givemoney"), group=9999)
async def givemoney(client: Client, message: Message):
    sender_id = message.from_user.id

    # Check if the sender is the OWNER_ID or a sudo user
    if sender_id not in [OWNER_ID] + sudo_users:
        await message.reply_text("You are not authorized to use this command.")
        return

    args = message.command

    if len(args) < 2:
        await message.reply_text("Usage: /givemoney <amount> [@username/user_id] or reply to a user.")
        return

    try:
        amount = int(args[1])
        if amount <= 0 or amount > 999999999999999999:
            raise ValueError
    except ValueError:
        await message.reply_text("Invalid amount. Please enter a positive number between 1 and 999999999999999999.")
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

    # Give the coins and update recipient balance only
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}})

    updated_recipient_balance, _, _, _ = await get_balance(recipient_id)

    # Send confirmation
    await message.reply_text(
        f"✅ You gave {amount} coins to @{html.escape(recipient_username or str(recipient_id))}."
    )

    await client.send_message(
        chat_id=recipient_id,
        text=f"🎉 You received {amount} coins from @{message.from_user.username}! "
        f"\n💰 Your New Balance: {updated_recipient_balance} coins"
    )


@app.on_message(filters.command("deletemoney"), group=9999)
async def deletemoney(client: Client, message: Message):
    sender_id = message.from_user.id

    # Check if the sender is the OWNER_ID or a sudo user
    if sender_id not in [OWNER_ID] + sudo_users:
        await message.reply_text("You are not authorized to use this command.")
        return

    args = message.command

    if len(args) < 2:
        await message.reply_text("Usage: /deletemoney <amount> [@username/user_id] or reply to a user.")
        return

    try:
        amount = int(args[1])
        if amount <= 0 or amount > 999999999999999999:
            raise ValueError
    except ValueError:
        await message.reply_text("Invalid amount. Please enter a positive number between 1 and 999999999999999999.")
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

    recipient_balance, _, _, _ = await get_balance(recipient_id)
    if recipient_balance < amount:
        await message.reply_text("Recipient has insufficient balance.")
        return

    # Deduct the amount from the recipient's balance
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': -amount}})

    updated_recipient_balance, _, _, _ = await get_balance(recipient_id)

    # Send confirmation
    await message.reply_text(
        f"✅ You deleted {amount} coins from @{html.escape(recipient_username or str(recipient_id))}."
    )

    await client.send_message(
        chat_id=recipient_id,
        text=f"⚠️ {amount} coins were deducted from your balance by @{message.from_user.username}.\n"
             f"💰 Your New Balance: {updated_recipient_balance} coins"
    )

    
    
@app.on_message(filters.command("mix"))
async def mix(client: Client, message: Message):
    user_id = message.from_user.id
    user_balance, user_black_stars, user_white_stars, user_golden_stars = await get_balance(user_id)

    if user_black_stars < 3 or user_white_stars < 3:
        await message.reply_text("You need at least 3 black stars and 3 white stars to mix.")
        return

    await user_collection.update_one({'id': user_id}, {'$inc': {'black_stars': -3, 'white_stars': -3, 'golden_stars': 1}})

    updated_balance, updated_black_stars, updated_white_stars, updated_golden_stars = await get_balance(user_id)

    await message.reply_text(
        f"⭐ You have successfully mixed 3 black stars and 3 white stars into 1 golden star!"
        f"\n★ Black Stars: {updated_black_stars}\n☆ White Stars: {updated_white_stars}\n⭐ Golden Stars: {updated_golden_stars}"
    )

@app.on_message(filters.command("exchange"))
async def exchange(client: Client, message: Message):
    user_id = message.from_user.id
    user_balance, user_black_stars, user_white_stars, user_golden_stars = await get_balance(user_id)

    if user_golden_stars < 100:
        await message.reply_text("❌ You need at least 100 golden stars to exchange.")
        return

    # Remove 100 golden stars and add 10,000 coins
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'golden_stars': -100, 'balance': 10000}}
    )

    updated_balance, updated_black_stars, updated_white_stars, updated_golden_stars = await get_balance(user_id)

    await message.reply_text(
        f"🎉 Exchange successful! You received 10,000 coins for 100 golden stars."
        f"\n💰 New Balance: {updated_balance} coins"
        f"\n⭐ Remaining Golden Stars: {updated_golden_stars}"
    )
    
