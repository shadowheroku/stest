from pyrogram import Client, filters
import datetime
from pyrogram.types import Message
from hasnainkk import app, db  # Importing your existing client and database

# Owner IDs
OWNERS = [6346273488, 6138142369, 5846676239]

# Database collection for blocked users
blocked_users = db.blocked_users

# Helper function to check if user is owner
def is_owner(user_id: int) -> bool:
    return user_id in OWNERS

# Block command
@app.on_message(filters.command("block"))
async def block_user(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply("⚠️ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply("❌ Please provide a username/user ID to block.\nUsage: /block [username/userid]")
        return
    
    target = message.command[1]
    try:
        # Try to parse as user ID
        user_id = int(target)
        user = await client.get_users(user_id)
    except ValueError:
        # Treat as username
        try:
            user = await client.get_users(target)
            user_id = user.id
        except Exception as e:
            await message.reply(f"❌ User not found: {e}")
            return
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        return
    
    # Check if already blocked
    if await blocked_users.find_one({"user_id": user_id}):
        await message.reply(f"ℹ️ User {user.first_name} is already blocked.")
        return
    
    # Add to blocked list
    await blocked_users.insert_one({
        "user_id": user_id,
        "first_name": user.first_name,
        "username": user.username,
        "blocked_by": message.from_user.id,
        "timestamp": datetime.datetime.now()
    })
    
    await message.reply(f"✅ Successfully blocked {user.first_name} (ID: {user_id}). They can no longer use the bot.")

# Unblock command
@app.on_message(filters.command("unblock"))
async def unblock_user(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply("⚠️ You are not authorized to use this command.")
        return
    
    if len(message.command) < 2:
        await message.reply("❌ Please provide a username/user ID to unblock.\nUsage: /unblock [username/userid]")
        return
    
    target = message.command[1]
    try:
        # Try to parse as user ID
        user_id = int(target)
        user = await client.get_users(user_id)
    except ValueError:
        # Treat as username
        try:
            user = await client.get_users(target)
            user_id = user.id
        except Exception as e:
            await message.reply(f"❌ User not found: {e}")
            return
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        return
    
    # Check if actually blocked
    if not await blocked_users.find_one({"user_id": user_id}):
        await message.reply(f"ℹ️ User {user.first_name} is not blocked.")
        return
    
    # Remove from blocked list
    await blocked_users.delete_one({"user_id": user_id})
    
    await message.reply(f"✅ Successfully unblocked {user.first_name} (ID: {user_id}). They can now use the bot again.\nFor appeal message @IFights")

# Blocklist command
@app.on_message(filters.command("blocklist"))
async def block_list(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        await message.reply("⚠️ You are not authorized to use this command.")
        return
    
    blocked = blocked_users.find()
    count = await blocked_users.count_documents({})
    
    if count == 0:
        await message.reply("ℹ️ No users are currently blocked.")
        return
    
    text = f"📋 Blocked Users List ({count}):\n\n"
    async for user in blocked:
        text += f"- {user['first_name']} (ID: {user['user_id']})\n"
    
    await message.reply(text)

# Middleware to check if user is blocked
@app.on_message((filters.private | filters.group) & ~filters.user(OWNERS))
async def check_blocked(client: Client, message: Message):
    user_id = message.from_user.id
    if await blocked_users.find_one({"user_id": user_id}):
        await message.stop_propagation() 
