import os
import random
import time
import string
import requests
from datetime import datetime, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from hasnainkk import app, db, LOGGER_ID, GROUP_ID, collection as character_collection, user_collection
from hasnainkk.unit.zyro_help import HELP_DATA
from hasnainkk import PHOTO_URL

# Video List for Random Selection
NEXI_VID = [
    "https://telegra.ph/file/1a3c152717eb9d2e94dc2.mp4",
    "https://graph.org/file/ba7699c28dab379b518ca.mp4",
    "https://graph.org/file/83ebf52e8bbf138620de7.mp4",
    "https://graph.org/file/82fd67aa56eb1b299e08d.mp4",
    "https://graph.org/file/318eac81e3d4667edcb77.mp4",
    "https://graph.org/file/7c1aa59649fbf3ab422da.mp4",
    "https://graph.org/file/2a7f857f31b32766ac6fc.mp4",
]

RAIDEN = "https://files.catbox.moe/dl3muf.mp4"

# Initialize collections
temp_links_collection = db.temp_link
user_drops_collection = db.user_drop
backup_collection = db.user_backups
glitch_logs_collection = db.glitch_logs

# Shortener configuration
SHORTNER_URL = "inshorturl.com"
SHORTNER_API = "4b57020954cb5431b310d1d5f2637d11edd3290a"

# Cooldown tracking
user_cooldowns = {}
OWNER_IDS = [6138142369, 1805959544, 1284920298, 5881613383, 5907205317, 6346273488]

# Group ID for notifications
NOTIFICATION_GROUP = -1002517018576

# Uptime tracking
START_TIME = time.time()

def get_uptime():
    uptime_seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def generate_random_alphanumeric():
    """Generate a random 8-letter alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

def get_short(url):
    """Shorten URL using the shortener service"""
    try:
        rget = requests.get(
            f"https://{SHORTNER_URL}/api?api={SHORTNER_API}"
            f"&url={url}&alias={generate_random_alphanumeric()}"
        )
        rjson = rget.json()
        if rjson.get("status") == "success" or rget.status_code == 200:
            return rjson["shortenedUrl"]
        return url
    except Exception as e:
        print(f"Shortener Error: {e}")
        return url

async def create_temp_link(reward_data, reward_type, character_data=None):
    """Create temporary claim link"""
    token = generate_random_alphanumeric()
    expires_at = datetime.now() + timedelta(minutes=30)
    
    await temp_links_collection.insert_one({
        'token': token,
        'reward_data': reward_data,
        'reward_type': reward_type,
        'expires_at': expires_at,
        'character_data': character_data,
        'created_at': datetime.now()
    })
    
    return token

async def is_token_valid(token):
    """Check if token is valid and not expired"""
    link_data = await temp_links_collection.find_one({'token': token})
    if not link_data:
        return False
    
    if datetime.now() > link_data['expires_at']:
        await temp_links_collection.delete_one({'token': token})
        return False
    
    return True

async def get_reward_data(token):
    """Get reward data for valid token"""
    link_data = await temp_links_collection.find_one({'token': token})
    if link_data:
        return {
            'type': link_data['reward_type'],
            'data': link_data['reward_data'],
            'character_data': link_data.get('character_data')
        }
    return None

async def delete_temp_link(token):
    """Remove used token from database"""
    await temp_links_collection.delete_one({'token': token})

async def track_user_drop(user_id, token, link):
    """Track user's drop and store in database"""
    await user_drops_collection.update_one(
        {'user_id': user_id},
        {'$set': {
            'last_drop_token': token,
            'last_drop_link': link,
            'claimed': False,
            'created_at': datetime.now()
        }},
        upsert=True
    )

async def has_unclaimed_drop(user_id):
    """Check if user has an unclaimed drop"""
    drop_data = await user_drops_collection.find_one({'user_id': user_id})
    if drop_data and not drop_data.get('claimed', True):
        # Check if the drop is still valid (not expired)
        link_data = await temp_links_collection.find_one({'token': drop_data['last_drop_token']})
        if link_data and datetime.now() <= link_data['expires_at']:
            return drop_data
    return None

async def mark_drop_claimed(user_id):
    """Mark user's drop as claimed"""
    await user_drops_collection.update_one(
        {'user_id': user_id},
        {'$set': {'claimed': True}}
)


async def backup_user_harem(user_id):
    """Backup user's harem before deletion"""
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        return False
    
    backup_data = {
        "user_id": user_id,
        "backup_data": user_data,
        "backup_time": datetime.now(),
        "restored": False
    }
    
    await backup_collection.insert_one(backup_data)
    return True

async def restore_user_harem(user_id):
    """Restore user's harem from backup"""
    backup_data = await backup_collection.find_one(
        {"user_id": user_id, "restored": False},
        sort=[("backup_time", -1)]
    )
    
    if not backup_data:
        return False
    
    await user_collection.replace_one(
        {"id": user_id},
        backup_data["backup_data"],
        upsert=True
    )
    
    await backup_collection.update_one(
        {"_id": backup_data["_id"]},
        {"$set": {"restored": True}}
    )
    
    return True


async def log_glitch_activity(user_id, activity_type, details):
    """Log suspicious activity for monitoring"""
    await glitch_logs_collection.insert_one({
        "user_id": user_id,
        "type": activity_type,
        "details": details,
        "timestamp": datetime.now(),
        "action_taken": False
    })

async def check_for_glitch_activity(user_id):
    """Check if user has suspicious activity patterns"""
    recent_drops = await user_drops_collection.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": datetime.now() - timedelta(minutes=5)}
    })
    
    if recent_drops > 3:
        await log_glitch_activity(user_id, "rapid_drops", f"{recent_drops} drops in 5 minutes")
        return True
    
    user_data = await user_collection.find_one({"id": user_id})
    if user_data:
        total_chars = len(user_data.get("characters", []))
        if total_chars > 1000:
            await log_glitch_activity(user_id, "excessive_characters", f"{total_chars} characters")
            return True
    
    return False



"""
async def auto_handle_glitches(user_id):
    if await check_for_glitch_activity(user_id):
        await backup_user_harem(user_id)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"characters": []}}
        )
        try:
            await app.send_message(
                user_id,
                "⚠️ Your harem has been reset due to detected suspicious activity.\n\n"
                "If this was a mistake, please contact @IFights with proof.\n"
                "Exploiting glitches will result in permanent loss."
            )
        except:
            pass
        return True
    return False
"""
async def auto_handle_glitches(user_id):
    """Automatically handle glitch exploitation with detailed logging"""
    client = app
    if await check_for_glitch_activity(user_id):
        # Get user details before taking action
        try:
            user = await client.get_users(user_id)
            username = f"@{user.username}" if user.username else "No username"
            first_name = user.first_name or "Unknown"
        except:
            username = "Unknown"
            first_name = "Unknown"

        # Backup first
        await backup_user_harem(user_id)
        
        # Get the glitch reason from logs
        glitch_log = await glitch_logs_collection.find_one(
            {"user_id": user_id, "action_taken": False},
            sort=[("timestamp", -1)]
        )
        reason = glitch_log.get("type", "suspicious_activity") if glitch_log else "suspicious_activity"
        proof = glitch_log.get("details", "automatic_detection") if glitch_log else "automatic_detection"

        # Wipe the harem
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"characters": []}}
        )

        # Mark log as action taken
        if glitch_log:
            await glitch_logs_collection.update_one(
                {"_id": glitch_log["_id"]},
                {"$set": {"action_taken": True}}
            )

        # Send notification to group
        ban_message = (
            "🚨 **AUTO HAREM RESET** 🚨\n\n"
            f"• User: {first_name} {username}\n"
            f"• ID: `{user_id}`\n"
            f"• Reason: `{reason}`\n"
            f"• Proof: `{proof}`\n\n"
            "__This action was taken automatically by the anti-exploit system__"
        )

        try:
            await client.send_message(
                NOTIFICATION_GROUP,  # Your existing notification group
                ban_message,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Error sending ban notification: {e}")

        # Notify the user
        try:
            await client.send_message(
                user_id,
                "⚠️ **Your harem has been reset** ⚠️\n\n"
                "Our system detected suspicious activity in your account.\n\n"
                "If this was a mistake, please contact @IFights with:\n"
                "- Screenshots of your recent drops\n"
                "- Explanation of what happened\n\n"
                "Note: Exploiting glitches violates our rules and may lead to permanent bans.",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        except:
            pass  # User may have blocked the bot
        
        return True
    return False

async def generate_start_message(client, message):
    bot_user = await client.get_me()
    bot_name = bot_user.first_name
    ping = round(time.time() - message.date.timestamp(), 2)
    uptime = get_uptime()
    
    caption = f"""***ʜᴇʟʟᴏ...***

***ɪ'ᴍ sɴᴀᴛᴄʜ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ʙᴏᴛ ᴀ ɢʀᴀʙ ʙᴏᴛ.....

ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ɪ ᴡɪʟʟ sᴇɴᴅ ʀᴀɴᴅᴏᴍ ᴄʜᴀʀᴀᴄᴛᴇʀs ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ...

ᴛᴀᴘ ᴏɴ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs...

ᴍᴜsᴛ Jᴏɪɴ :- @The_League_Of_Snatchers***


➺ ᴘɪɴɢ: {ping} ms
➺ ᴜᴘᴛɪᴍᴇ: {uptime}"""

    buttons = [
        [InlineKeyboardButton("Add to Your Group", url=f"https://t.me/{bot_user.username}?startgroup=true")],
        [InlineKeyboardButton("Support", url="https://t.me/Midexoz_Support"), 
         InlineKeyboardButton("Channel", url="https://t.me/MidexOzBotUpdates")],
        [InlineKeyboardButton("Help", callback_data="open_help")]
    ]
    
    return caption, InlineKeyboardMarkup(buttons)



@app.on_message(filters.command("start"), group=98888292927)
async def start_command(client, message):
    try:
        args = message.text.split()
        
        # Handle claim links
        if len(args) > 1 and args[1].startswith("claim_"):
            token = args[1][6:]
            
            # Check if token is valid
            if not await is_token_valid(token):
                return await message.reply("❌ Invalid or expired claim link. Please request a new one.")
            
            # Get reward data
            reward_data = await get_reward_data(token)
            if not reward_data:
                return await message.reply("❌ Reward data not found.")
            
            user_id = message.from_user.id
            reward_type = reward_data['type']
            
            if reward_type == "character":
                character_data = reward_data['character_data']
                if not character_data:
                    return await message.reply("❌ Character data not found.")
                
                # Check if user already has this character
                user_data = await user_collection.find_one({'id': user_id})
                if user_data:
                    if any(char.get('id') == character_data.get('id') for char in user_data.get('characters', [])):
                        await delete_temp_link(token)
                        return await message.reply("⚠️ You already have this character in your collection!")
                    
                    # Add character to existing user
                    await user_collection.update_one(
                        {'id': user_id},
                        {'$push': {'characters': character_data}}
                    )
                else:
                    # Create new user with this character
                    await user_collection.insert_one({
                        'id': user_id,
                        'username': message.from_user.username,
                        'first_name': message.from_user.first_name,
                        'characters': [character_data],
                        'balance': 0,
                        'black_stars': 0,
                        'white_stars': 0,
                        'golden_stars': 0
                    })
                
                await delete_temp_link(token)
                await mark_drop_claimed(user_id)
                
                # Prepare the caption
                caption = (
                    f"🎉 You have successfully claimed {character_data.get('name', 'Unknown')}!\n\n"
                    f"📛 Name: {character_data.get('name', 'Unknown')}\n"
                    f"🌈 Anime: {character_data.get('anime', 'Unknown')}\n"
                    f"✨ Rarity: {character_data.get('rarity', 'Unknown')}\n\n"
                    f"🆔 ID: {character_data.get('id', 'Unknown')}"
                )
                
                # Send media with caption
                if 'vid_url' in character_data:
                    await message.reply_video(
                        video=character_data['vid_url'],
                        caption=caption,
                        parse_mode=enums.ParseMode.HTML
                    )
                elif 'img_url' in character_data:
                    await message.reply_photo(
                        photo=character_data['img_url'],
                        caption=caption,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    await message.reply(caption)
                return
            
            elif reward_type == "money":
                amount = reward_data['data']
                if not isinstance(amount, int):
                    return await message.reply("❌ Invalid money amount.")
                
                await user_collection.update_one(
                    {'id': user_id},
                    {'$inc': {'balance': amount}},
                    upsert=True
                )
                
                await delete_temp_link(token)
                await mark_drop_claimed(user_id)
                await auto_handle_glitches(user_id)  # NEW: Check for glitches after claim

                await message.reply(
                    f"💰 Money claimed successfully!\n\n"
                    f"➕ {amount} coins added to your balance."
                )
                return
                  
            elif reward_type == "star":
                star_data = reward_data['data']
                if not isinstance(star_data, dict):
                    return await message.reply("❌ Invalid star data.")
                
                star_type = star_data.get('type')
                count = star_data.get('count', 1)
                star_emoji = {"black": "★", "white": "☆", "golden": "🌟"}.get(star_type, "⭐")
                
                await user_collection.update_one(
                    {'id': user_id},
                    {'$inc': {f"{star_type}_stars": count}},
                    upsert=True
                )
                
                await delete_temp_link(token)
                await mark_drop_claimed(user_id)
                
                await message.reply(
                    f"⭐ Stars claimed successfully!\n\n"
                    f"➕ {count} {star_type} star{'' if count == 1 else 's'} {star_emoji} added to your collection."
                )
                return
            
            return await message.reply("❌ Invalid reward type.")
        
        # Normal start command
        caption, buttons = await generate_start_message(client, message)
        image = random.choice(PHOTO_URL)
        
        await app.send_message(
            chat_id=GROUP_ID,
            text=f"{message.from_user.mention} started the bot.\nUser ID: {message.from_user.id}\nUsername: @{message.from_user.username}",
        )
        
        await message.reply_photo(
            photo=image,
            caption=caption,
            reply_markup=buttons
        )
        
    except Exception as e:
        await message.reply(f"❌ An error occurred: {str(e)}")
        print(f"Error in start_command: {e}")

"""        
@app.on_message(filters.command(["drop", "sdrop"]), group=992929272828)
async def sdrop_command(client, message: Message):
    try:
        user_id = message.from_user.id
        current_time = time.time()

        # Special handling for user 6346273488 - no cooldown or unclaimed drop check
        if user_id != 6346273488:
            # Check for unclaimed drops
            unclaimed_drop = await has_unclaimed_drop(user_id)
            if unclaimed_drop:
                return await message.reply(
                    "⚠️ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴘʀᴇᴠɪᴏᴜs ᴅʀᴏᴘ ʏᴇᴛ!\n"
                    "ᴘʟᴇᴀsᴇ ᴠɪsɪᴛ ᴛʜᴇ ʟɪɴᴋ ᴀɢᴀɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ", url=unclaimed_drop['last_drop_link'])]
                    ])
                )

            # Check cooldown
  #          if user_id in user_cooldowns:
 #               last_used = user_cooldowns[user_id]
#                cooldown_remaining = 1800 - (current_time - last_used)
  #              if cooldown_remaining > 0:
   #                 hours = int(cooldown_remaining // 3600)
   #                 minutes = int((cooldown_remaining % 3600) // 60)
    #                seconds = int(cooldown_remaining % 60)
    #                return await message.reply(
    #                    f"⏳ You can use this command again in {hours}h {minutes}m {seconds}s"
    #                )
    #        user_cooldowns[user_id] = current_time

        # Random reward selection with adjusted probabilities
        reward_type = random.choices(
            ["character", "money", "star"],
            weights=[40, 40, 20],  # 40% character, 40% money, 20% star
            k=1
        )[0]
        
        if reward_type == "character":
            all_chars = [char async for char in character_collection.find({})]
            if not all_chars:
                return await message.reply("❌ No characters found in the database.")
            
            character = random.choice(all_chars)
            token = await create_temp_link(character, "character", character)
            bot_username = (await app.get_me()).username
            long_link = f"https://t.me/{bot_username}?start=claim_{token}"
            short_link = get_short(long_link)
            
            # Store drop info for unclaimed drop check (except for special user)
            if user_id != 6346273488:
                await track_user_drop(user_id, token, short_link)

            # Notify group about the drop usage
            try:
                await app.send_message(
                    NOTIFICATION_GROUP,
                    f"#NEW_DROP\n\n🚀 New /sdrop used by user:\n"
                    f"👤 User: {message.from_user.mention}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📛 Username: @{message.from_user.username}\n"
                    f"🔗 Short Link: {short_link}\n"
                    f"🔗 Long Link: {long_link}\n\n"
                    f"🎁 Reward Type: Character\n"
                    f"📛 Character: {character.get('name', 'Unknown')}\n"
                    f"🌈 Anime: {character.get('anime', 'Unknown')}\n"
                    f"🆔 Character Id: {character.get('id', 'Unknown')}"
                )
            except Exception as e:
                print(f"Error sending notification to group: {e}")                
            
            await message.reply(
                "🎲 ᴛʀʏ ʏᴏᴜʀ ʟᴜᴄᴋ ᴀɴᴅ ɢᴇᴛ ᴀ ʀᴇᴡᴀʀᴅ!\n"
                "🎁 ᴏᴘᴇɴ ʏᴏᴜʀ ғʀᴇᴇ ᴄʟᴀɪᴍ ᴛᴏ ᴅɪsᴄᴏᴠᴇʀ ᴡʜᴀᴛ ʏᴏᴜ'ʟʟ ɢᴇᴛ.\n\n"
                "ɪᴛ ᴄᴏᴜʟᴅ ʙᴇ:\n"
                "• 🧑‍🎤 ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ\n"
                "• 💰 ᴍᴏɴᴇʏ\n"
                "• ⭐ ᴀ ᴛʏᴘᴇ ᴏғ sᴛᴀʀ (ʙʟᴀᴄᴋ/ᴡʜɪᴛᴇ/ɢᴏʟᴅᴇɴ)\n\n"
                "📝 ɴᴏᴛᴇ: ʏᴏᴜ ᴄᴀɴ ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ ᴏɴʟʏ ᴏɴᴄᴇ ᴇᴠᴇʀʏ 30 ᴍɪɴᴜᴛᴇs!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ", url=short_link)]
                ])
            )
            
        elif reward_type == "money":
            amount = random.randint(5000, 20000)  # Random amount between 5k-20k
            token = await create_temp_link(amount, "money")
            bot_username = (await app.get_me()).username
            long_link = f"https://t.me/{bot_username}?start=claim_{token}"
            short_link = get_short(long_link)
            
            # Store drop info for unclaimed drop check (except for special user)
            if user_id != 6346273488:
                await track_user_drop(user_id, token, short_link)

            # Notify group about the drop usage
            try:
                await app.send_message(
                    NOTIFICATION_GROUP,
                    f"#NEW_DROP\n\n🚀 New /sdrop used by user:\n"
                    f"👤 User: {message.from_user.mention}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📛 Username: @{message.from_user.username}\n"
                    f"🔗 Short Link: {short_link}\n"
                    f"🔗 Long Link: {long_link}\n\n"
                    f"🎁 Reward Type: Money\n"
                    f"💰 Amount: {amount} coins"
                )
            except Exception as e:
                print(f"Error sending notification to group: {e}")
                
            await message.reply(
                "🎲 ᴛʀʏ ʏᴏᴜʀ ʟᴜᴄᴋ ᴀɴᴅ ɢᴇᴛ ᴀ ʀᴇᴡᴀʀᴅ!\n"
                "🎁 ᴏᴘᴇɴ ʏᴏᴜʀ ғʀᴇᴇ ᴄʟᴀɪᴍ ᴛᴏ ᴅɪsᴄᴏᴠᴇʀ ᴡʜᴀᴛ ʏᴏᴜ'ʟʟ ɢᴇᴛ.\n\n"
                "ɪᴛ ᴄᴏᴜʟᴅ ʙᴇ:\n"
                "• 🧑‍🎤 ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ\n"
                "• 💰 ᴍᴏɴᴇʏ\n"
                "• ⭐ ᴀ ᴛʏᴘᴇ ᴏғ sᴛᴀʀ (ʙʟᴀᴄᴋ/ᴡʜɪᴛᴇ/ɢᴏʟᴅᴇɴ)\n\n"
                "📝 ɴᴏᴛᴇ: ʏᴏᴜ ᴄᴀɴ ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ ᴏɴʟʏ ᴏɴᴄᴇ ᴇᴠᴇʀʏ 30 ᴍɪɴᴜᴛᴇs!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ", url=short_link)]
                ])
            )
            
        elif reward_type == "star":
            star_types = ["black", "white", "golden"]
            star_type = random.choices(
                star_types,
                weights=[70, 25, 5],  # 70% black, 25% white, 5% golden
                k=1
            )[0]
            
            star_data = {
                'type': star_type,
                'count': 1
            }
            
            token = await create_temp_link(star_data, "star")
            bot_username = (await app.get_me()).username
            long_link = f"https://t.me/{bot_username}?start=claim_{token}"
            short_link = get_short(long_link)
            
            # Track the user's drop (except for special user)
            if user_id != 6346273488:
                await track_user_drop(user_id, token, short_link)

            # Notify group about the drop usage
            try:
                await app.send_message(
                    NOTIFICATION_GROUP,
                    f"#NEW_DROP\n\n🚀 New /sdrop used by user:\n"
                    f"👤 User: {message.from_user.mention}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📛 Username: @{message.from_user.username}\n"
                    f"🔗 Short Link: {short_link}\n"
                    f"🔗 Long Link: {long_link}\n\n"
                    f"🎁 Reward Type: Star\n"
                    f"⭐ Type: {star_type} star"
                )
            except Exception as e:
                print(f"Error sending notification to group: {e}")
                
            await message.reply(
                "🎲 ᴛʀʏ ʏᴏᴜʀ ʟᴜᴄᴋ ᴀɴᴅ ɢᴇᴛ ᴀ ʀᴇᴡᴀʀᴅ!\n"
                "🎁 ᴏᴘᴇɴ ʏᴏᴜʀ ғʀᴇᴇ ᴄʟᴀɪᴍ ᴛᴏ ᴅɪsᴄᴏᴠᴇʀ ᴡʜᴀᴛ ʏᴏᴜ'ʟʟ ɢᴇᴛ.\n\n"
                "ɪᴛ ᴄᴏᴜʟᴅ ʙᴇ:\n"
                "• 🧑‍🎤 ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ\n"
                "• 💰 ᴍᴏɴᴇʏ\n"
                "• ⭐ ᴀ ᴛʏᴘᴇ ᴏғ sᴛᴀʀ (ʙʟᴀᴄᴋ/ᴡʜɪᴛᴇ/ɢᴏʟᴅᴇɴ)\n\n"
                "📝 ɴᴏᴛᴇ: ʏᴏᴜ ᴄᴀɴ ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ ᴏɴʟʏ ᴏɴᴄᴇ ᴇᴠᴇʀʏ 30 ᴍɪɴᴜᴛᴇs!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ", url=short_link)]
                ])
            )
            
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
        print(f"Error in sdrop_command: {e}")



"""
@app.on_message(filters.command(["drop", "sdrop"]), group=992929272828)
async def sdrop_command(client, message: Message):
    try:
        user_id = message.from_user.id
        current_time = time.time()

        # Special handling for user 6346273488 - no cooldown or unclaimed drop check
        if user_id != 6346273488:
            # Check for unclaimed drops
            unclaimed_drop = await has_unclaimed_drop(user_id)
            if unclaimed_drop:
                return await message.reply(
                    "⚠️ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴘʀᴇᴠɪᴏᴜs ᴅʀᴏᴘ ʏᴇᴛ!\n"
                    "ᴘʟᴇᴀsᴇ ᴠɪsɪᴛ ᴛʜᴇ ʟɪɴᴋ ᴀɢᴀɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ", url=unclaimed_drop['last_drop_link'])]
                    ])
                )

            # Cooldown check (30 minutes)
            if user_id in user_cooldowns:
                last_used = user_cooldowns[user_id]
                cooldown_remaining = 1800 - (current_time - last_used)
                if cooldown_remaining > 0:
                    hours = int(cooldown_remaining // 3600)
                    minutes = int((cooldown_remaining % 3600) // 60)
                    seconds = int(cooldown_remaining % 60)
                    return await message.reply(
                        f"⏳ You can use this command again in {hours}h {minutes}m {seconds}s"
                    )
            user_cooldowns[user_id] = current_time

        # Random reward selection
        reward_type = random.choices(
            ["character", "money", "star"],
            weights=[40, 40, 20],
            k=1
        )[0]

        bot_username = (await app.get_me()).username

        if reward_type == "character":
            all_chars = [char async for char in character_collection.find({})]
            if not all_chars:
                return await message.reply("❌ No characters found in the database.")

            character = random.choice(all_chars)
            token = await create_temp_link(character, "character", character)
            long_link = f"https://t.me/{bot_username}?start=claim_{token}"
            short_link = get_short(long_link)

            if user_id != 6346273488:
                await track_user_drop(user_id, token, short_link)

            await app.send_message(
                NOTIFICATION_GROUP,
                f"#NEW_DROP\n\n🚀 New /sdrop used by user:\n"
                f"👤 User: {message.from_user.mention}\n"
                f"🆔 ID: {user_id}\n"
                f"📛 Username: @{message.from_user.username}\n"
                f"🔗 Short Link: {short_link}\n"
                f"🔗 Long Link: {long_link}\n\n"
                f"🎁 Reward Type: Character\n"
                f"📛 Character: {character.get('name', 'Unknown')}\n"
                f"🌈 Anime: {character.get('anime', 'Unknown')}\n"
                f"🆔 Character Id: {character.get('id', 'Unknown')}"
            )

        elif reward_type == "money":
            amount = random.randint(5000, 20000)
            token = await create_temp_link(amount, "money")
            long_link = f"https://t.me/{bot_username}?start=claim_{token}"
            short_link = get_short(long_link)

            if user_id != 6346273488:
                await track_user_drop(user_id, token, short_link)

            await app.send_message(
                NOTIFICATION_GROUP,
                f"#NEW_DROP\n\n🚀 New /sdrop used by user:\n"
                f"👤 User: {message.from_user.mention}\n"
                f"🆔 ID: {user_id}\n"
                f"📛 Username: @{message.from_user.username}\n"
                f"🔗 Short Link: {short_link}\n"
                f"🔗 Long Link: {long_link}\n\n"
                f"🎁 Reward Type: Money\n"
                f"💰 Amount: {amount} coins"
            )

        elif reward_type == "star":
            star_types = ["black", "white", "golden"]
            star_type = random.choices(star_types, weights=[70, 25, 5], k=1)[0]

            star_data = {'type': star_type, 'count': 1}
            token = await create_temp_link(star_data, "star")
            long_link = f"https://t.me/{bot_username}?start=claim_{token}"
            short_link = get_short(long_link)

            if user_id != 6346273488:
                await track_user_drop(user_id, token, short_link)

            await app.send_message(
                NOTIFICATION_GROUP,
                f"#NEW_DROP\n\n🚀 New /sdrop used by user:\n"
                f"👤 User: {message.from_user.mention}\n"
                f"🆔 ID: {user_id}\n"
                f"📛 Username: @{message.from_user.username}\n"
                f"🔗 Short Link: {short_link}\n"
                f"🔗 Long Link: {long_link}\n\n"
                f"🎁 Reward Type: Star\n"
                f"⭐ Type: {star_type} star"
            )

        # Final reply to user
#        await auto_handle_glitches(user_id)
        await message.reply(
            "🎲 ᴛʀʏ ʏᴏᴜʀ ʟᴜᴄᴋ ᴀɴᴅ ɢᴇᴛ ᴀ ʀᴇᴡᴀʀᴅ!\n"
            "🎁 ᴏᴘᴇɴ ʏᴏᴜʀ ғʀᴇᴇ ᴄʟᴀɪᴍ ᴛᴏ ᴅɪsᴄᴏᴠᴇʀ ᴡʜᴀᴛ ʏᴏᴜ'ʟʟ ɢᴇᴛ.\n\n"
            "ɪᴛ ᴄᴏᴜʟᴅ ʙᴇ:\n"
            "• 🧑‍🎤 ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ\n"
            "• 💰 ᴍᴏɴᴇʏ\n"
            "• ⭐ ᴀ ᴛʏᴘᴇ ᴏғ sᴛᴀʀ (ʙʟᴀᴄᴋ/ᴡʜɪᴛᴇ/ɢᴏʟᴅᴇɴ)\n\n"
            "📝 ɴᴏᴛᴇ: ʏᴏᴜ ᴄᴀɴ ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ ᴏɴʟʏ ᴏɴᴄᴇ ᴇᴠᴇʀʏ 30 ᴍɪɴᴜᴛᴇs!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 ᴄʟᴀɪᴍ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅ", url=short_link)]
            ])
        )

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
        print(f"Error in sdrop_command: {e}")


@app.on_message(filters.command("return") & filters.user(OWNER_IDS))
async def restore_harem_command(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("Usage: /return <user_id>")
        
        user_id = int(message.command[1])
        if await restore_user_harem(user_id):
            await message.reply(f"Successfully restored harem for user {user_id}")
            try:
                await app.send_message(
                    user_id,
                    "🎉 Your harem has been restored by the admin.\n\n"
                    "Please avoid any suspicious activity to prevent future issues."
                )
            except:
                pass
        else:
            await message.reply(f"No backup found for user {user_id}")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# Help system functions
def find_help_modules():
    buttons = []
    
    for module_name, module_data in HELP_DATA.items():
        button_name = module_data.get("HELP_NAME", "Unknown")
        buttons.append(InlineKeyboardButton(button_name, callback_data=f"help_{module_name}"))

    return [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

# 🔹 Help Button Click Handler
@app.on_callback_query(filters.regex("^open_help$"))
async def show_help_menu(client, query: CallbackQuery):
    time.sleep(1)
    buttons = find_help_modules()
    buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back_to_home")])

    await query.message.edit_text(
        """*ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ғᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴩ.

ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /""",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_message(filters.command("help"), group=97817817)
async def help_command(client, message: Message):
    # Simulate a delay (if needed)
    time.sleep(1)
    
    # Fetch the help modules and add a back button
    buttons = find_help_modules()
    buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back_to_home")])

    # Edit the message with the help menu
    await message.reply_text(
        """*ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ғᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴩ.

ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /""",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 🔹 Individual Module Help Handler (Optimized)
@app.on_callback_query(filters.regex(r"^help_(.+)"))
async def show_help(client, query: CallbackQuery):
    time.sleep(1)
    module_name = query.data.split("_", 1)[1]
    
    try:
        module_data = HELP_DATA.get(module_name, {})
        help_text = module_data.get("HELP", "Is module ka koi help nahi hai.")
        buttons = [[InlineKeyboardButton("⬅ Back", callback_data="open_help")]]
        
        await query.message.edit_text(f"**{module_name} Help:**\n\n{help_text}", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await query.answer("Help load karne me error aayi!")

# 🔹 Back to Home (Edit Message Instead of Sending New)
@app.on_callback_query(filters.regex("^back_to_home$"))
async def back_to_home(client, query: CallbackQuery):
    time.sleep(1) 
    caption, buttons = await generate_start_message(client, query.message)
    await query.message.edit_text(caption, reply_markup=buttons)
