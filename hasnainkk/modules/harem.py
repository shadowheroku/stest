from hasnainkk import *
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery
from itertools import groupby
import math
from html import escape
import random
from hasnainkk import collection, user_collection, application, app
from hasnainkk import BASE_API_URL as SERVER_BASE_URL
from hasnainkk import rarity_map2
from pyrogram import enums
import datetime

async def fetch_user_characters(user_id):
    user = await user_collection.find_one({"id": user_id})
    if not user or 'characters' not in user:
        return None, 'You have not guessed any characters yet.'
    characters = [c for c in user['characters'] if 'id' in c]
    if not characters:
        return None, 'No valid characters found in your collection.'
    return characters, None

import asyncio  # Import asyncio for sleep function



#from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_message(filters.command(["harem", "collection"]))
async def harem_access_check(client, message):
    user_id = message.from_user.id
    group_link = "https://t.me/the_league_of_snatchers"  # Replace with your group link
    
    try:
        # Strict membership check
        member = await client.get_chat_member("the_league_of_snatchers", user_id)
        if member.status in ["left", "kicked"]:
            raise UserNotParticipant  # Force join prompt
    except:
        # Send locked message with button
        lock_msg = await message.reply(
            "🔐 **Harem Locked** 🔐\n\n"
            "Join our group to unlock your collection!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✨ JOIN GROUP ✨", url=group_link)],
                [InlineKeyboardButton("🔄 I Joined", callback_data="joined_check")]
            ])
        )
        await asyncio.sleep(180)  # Delete after 180 sec
        await lock_msg.delete()
        return  # Exit - no harem access

    # Show harem only if joined
    msg = await display_harem(client, message, user_id, page=0, filter_rarity=None, is_initial=True)
    await asyncio.sleep(180)  # Auto-delete after 3 min
    await msg.delete()
  #  await msg.delete()
#async def display_harem(client, message, user_id, page, filter_rarity, is_initial=False, callback_query=None):
#    # Your existing harem display code goes here
   # pass

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_callback_query(filters.regex("joined_check"))
async def recheck_join(client, query):
    try:
        user_id = query.from_user.id
        await query.answer("⌛ Verifying...")  # Instant feedback
        
        # FAST CHECK (Uses cached data if possible)
        try:
            member = await client.get_chat_member("the_league_of_snatchers", user_id)
            is_member = member.status not in ["left", "kicked"]
        except:
            is_member = False  # Fail-safe

        if is_member:
            await query.message.delete()  # Delete lock screen IMMEDIATELY
            await query.answer("✅ Access granted! Use /harem again.", show_alert=True)
        else:
            await query.answer("❌ Still not in group! Click JOIN.", show_alert=True)
            
    except Exception as e:
        await query.answer("⚠️ Error! Try /harem again.", show_alert=True)


async def display_harem(client, message, user_id, page, filter_rarity, is_initial=False, callback_query=None):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            await message.reply_text(error)
            return

        # Sort characters by anime and ID
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))

        # Filter by rarity if specified
        if filter_rarity:
            characters = [c for c in characters if c.get('rarity') == filter_rarity]

        # Group characters by ID and count duplicates
        character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
        unique_characters = list({character['id']: character for character in characters}.values())
        total_pages = math.ceil(len(unique_characters) / 15)

        # Ensure page is within valid range
        if page < 0 or page >= total_pages:
            page = 0

        # Build harem message
        harem_message = f"<b>{escape(message.from_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"
        if filter_rarity:
            harem_message += f"<b>Filtered by: {filter_rarity}</b>\n"

        # Get characters for the current page
        current_characters = unique_characters[page * 15:(page + 1) * 15]
        current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

        # Add character details to the message
        for anime, chars in current_grouped_characters.items():
            harem_message += f'\n<b>{anime} {len(chars)}/{await collection.count_documents({"anime": anime})}</b>\n'
            for character in chars:
                count = character_counts[character['id']]
                rarity_emoji = rarity_map2.get(character.get('rarity'), '')
                harem_message += f'◈⌠{rarity_emoji}⌡ {character["id"]} {character["name"]} ×{count}\n'

        # Add inline buttons for collection and video-only collection
        keyboard = [
            [
                InlineKeyboardButton("Collection", switch_inline_query_current_chat=f"collection.{user_id}"),
                InlineKeyboardButton("💌 AMV", switch_inline_query_current_chat=f"collection.{user_id}.AMV")
            ]
        ]

        # Add navigation buttons if there are multiple pages
        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}"))
            keyboard.append(nav_buttons)

        # Add filter button
        keyboard.append([InlineKeyboardButton("Filter by Rarity", callback_data=f"filter:{user_id}")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Select a random character for the image/video
        image_character = None
        user = await user_collection.find_one({"id": user_id})
        if user and 'favorites' in user and user['favorites']:
            favorite_character_id = user['favorites'][0]
            image_character = next((c for c in characters if c['id'] == favorite_character_id), None)

        if not image_character:
            image_character = random.choice(characters) if characters else None

        # Send the harem message with media
        if is_initial:
            if image_character:
                if 'vid_url' in image_character:
                    await message.reply_video(
                        video=image_character['vid_url'],
                        caption=harem_message,
                        reply_markup=reply_markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                elif 'img_url' in image_character:
                    await message.reply_photo(
                        photo=image_character['img_url'],
                        caption=harem_message,
                        reply_markup=reply_markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    await message.reply_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await message.reply_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            # Handle callback query edits
            if image_character:
                if 'vid_url' in image_character:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(image_character['vid_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                elif 'img_url' in image_character:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(image_character['img_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                else:
                    await callback_query.message.edit_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await callback_query.message.edit_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("An error occurred. Please try again later.")

@app.on_callback_query(filters.regex(r"^harem"))
async def harem_callback(client, callback_query):
    try:
        data = callback_query.data
        _, page, user_id, filter_rarity = data.split(':')
        page = int(page)
        user_id = int(user_id)
        filter_rarity = None if filter_rarity == 'None' else filter_rarity

        if callback_query.from_user.id != user_id:
            await callback_query.answer("It's not your Harem!", show_alert=True)
            return

        await display_harem(client, callback_query.message, user_id, page, filter_rarity, is_initial=False, callback_query=callback_query)
    except Exception as e:
        print(f"Error in callback: {e}")

@app.on_callback_query(filters.regex(r"^filter"))
async def filter_callback(client, callback_query):
    try:
        _, user_id = callback_query.data.split(':')
        user_id = int(user_id)

        if callback_query.from_user.id != user_id:
            await callback_query.answer("It's not your Harem!", show_alert=True)
            return

        keyboard = []
        row = []
        for i, (rarity, emoji) in enumerate(rarity_map2.items(), 1):
            row.append(InlineKeyboardButton(emoji, callback_data=f"apply_filter:{user_id}:{rarity}"))
            if i % 4 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("Clear Filter", callback_data=f"apply_filter:{user_id}:None")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await callback_query.message.edit_text("Select a rarity to filter:", reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in filter callback: {e}")

@app.on_callback_query(filters.regex(r"^apply_filter"))
async def apply_filter_callback(client, callback_query):
    try:
        _, user_id, filter_rarity = callback_query.data.split(':')
        user_id = int(user_id)
        filter_rarity = None if filter_rarity == 'None' else filter_rarity

        if callback_query.from_user.id != user_id:
            await callback_query.answer("It's not your Harem!", show_alert=True)
            return

        await display_harem(client, callback_query.message, user_id, 0, filter_rarity, is_initial=False, callback_query=callback_query)
    except Exception as e:
        print(f"Error in apply_filter callback: {e}")


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

OWNER_IDS = [6346273488, 6138142369 , 6346273488 ]  # Owner IDs for permissions

@app.on_message(filters.command("deleteharem"))
async def delete_harem(client, message):
    try:
        # Check if the user is in OWNER_IDS
        if message.from_user.id not in OWNER_IDS:
            await message.reply_text("You don't have permission to perform this action.")
            return

        # Check if the user mentioned someone or replied to a message
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        elif message.text.split()[1].startswith('@'):
            # Extract user_id from username
            username = message.text.split()[1][1:]
            user = await client.get_users(username)
            user_id = user.id
        else:
            # Default to the sender's ID
            user_id = message.from_user.id

        # Create the confirmation message with inline buttons
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"confirm_delete:{user_id}:yes"),
                InlineKeyboardButton("Cancel", callback_data=f"confirm_delete:{user_id}:cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await message.reply_text(
            f"Are you sure you want to delete the entire harem for user ID {user_id}? This action cannot be undone.",
            reply_markup=reply_markup
        )

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("An error occurred. Please try again later.")

@app.on_callback_query(filters.regex(r"^confirm_delete"))
async def confirm_delete_callback(client, callback_query):
    try:
        # Get the data from callback query (user_id and action)
        _, user_id, action = callback_query.data.split(':')

        user_id = int(user_id)

        # Check if the user is in OWNER_IDS
        if callback_query.from_user.id not in OWNER_IDS:
            await callback_query.answer("You don't have permission to perform this action.", show_alert=True)
            return

        # Handle confirmation or cancellation
        if action == 'yes':
            # Delete the harem
            await user_collection.update_one({"id": user_id}, {"$set": {"characters": []}})
            await callback_query.message.edit_text(f"The entire harem for user ID {user_id} has been deleted and reset!")
        elif action == 'cancel':
            # Cancel the action
            await callback_query.message.edit_text("Action canceled. No changes were made.")

    except Exception as e:
        print(f"Error in callback: {e}")
        await callback_query.message.edit_text("An error occurred. Please try again later.")


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

OWNER_IDS = [6346273488, 6138142369]  # Owner IDs who can use transfer command

@app.on_message(filters.command("transfer"))
async def transfer_harem(client, message):
    try:
        # Check if the user is in OWNER_IDS
        if message.from_user.id not in OWNER_IDS:
            await message.reply_text("⚠️ Only bot owners can use this command.")
            return

        # Check command format
        if len(message.command) < 3:
            await message.reply_text("❌ Invalid format. Use:\n/transfer <from_user_id> <to_user_id>")
            return

        from_user_id = int(message.command[1])
        to_user_id = int(message.command[2])

        # Prevent self-transfer
        if from_user_id == to_user_id:
            await message.reply_text("❌ Cannot transfer to the same user!")
            return

        # Get both users' data
        from_user = await user_collection.find_one({"id": from_user_id})
        to_user = await user_collection.find_one({"id": to_user_id})

        # Check if source user exists and has collection
        if not from_user or 'characters' not in from_user or not from_user['characters']:
            await message.reply_text(f"❌ User {from_user_id} has no collection to transfer!")
            return

        # Create confirmation message
        confirm_text = (
            f"⚠️ **Harem Transfer Request** ⚠️\n\n"
            f"From: `{from_user_id}` (has {len(from_user['characters'])} characters)\n"
            f"To: `{to_user_id}`\n\n"
            f"**THIS WILL OVERWRITE THE DESTINATION USER'S EXISTING COLLECTION!**"
        )

        # Create inline keyboard for confirmation
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ CONFIRM", callback_data=f"transfer_confirm:{from_user_id}:{to_user_id}"),
                InlineKeyboardButton("❌ CANCEL", callback_data="transfer_cancel")
            ]
        ])

        await message.reply_text(confirm_text, reply_markup=keyboard)

    except ValueError:
        await message.reply_text("❌ Invalid user ID format. Must be numbers.")
    except Exception as e:
        print(f"Transfer Error: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

@app.on_callback_query(filters.regex(r"^transfer_confirm"))
async def transfer_confirm_callback(client, callback_query):
    try:
        # Only allow owners to confirm
        if callback_query.from_user.id not in OWNER_IDS:
            await callback_query.answer("⚠️ Only owners can confirm transfers!", show_alert=True)
            return

        # Parse callback data
        _, from_user_id, to_user_id = callback_query.data.split(':')
        from_user_id = int(from_user_id)
        to_user_id = int(to_user_id)

        # Get the source user's collection
        from_user = await user_collection.find_one({"id": from_user_id})
        if not from_user:
            await callback_query.message.edit_text("❌ Source user no longer exists!")
            return

        # Perform the transfer
        transfer_data = {
            "characters": from_user['characters'],
            "favorites": from_user.get('favorites', [])
        }

        # Update destination user (upsert=True creates if doesn't exist)
        await user_collection.update_one(
            {"id": to_user_id},
            {"$set": transfer_data},
            upsert=True
        )

        # Clear source user's collection
        await user_collection.update_one(
            {"id": from_user_id},
            {"$set": {"characters": [], "favorites": []}}
        )

        # Send success message
        success_msg = (
            f"♻️ **Transfer Complete** ♻️\n\n"
            f"• From: `{from_user_id}`\n"
            f"• To: `{to_user_id}`\n"
            f"• Characters Moved: {len(from_user['characters'])}\n\n"
            f"Source collection has been reset!"
        )

        await callback_query.message.edit_text(success_msg)

    except Exception as e:
        print(f"Transfer Confirm Error: {e}")
        await callback_query.message.edit_text("❌ Transfer failed! Please check logs.")

@app.on_callback_query(filters.regex(r"^transfer_cancel"))
async def transfer_cancel_callback(client, callback_query):
    # Only allow owners to cancel
    if callback_query.from_user.id not in OWNER_IDS:
        await callback_query.answer("⚠️ Only owners can cancel transfers!", show_alert=True)
        return
    
    await callback_query.message.edit_text("🚫 Transfer cancelled. No changes were made.")


from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

OWNER_IDS = [6346273488, 6138142369]  # Owner IDs

# Banned users collection (add this to your database setup)
banned_users = db['banned_users']

@app.on_message(filters.command("rmuser") & filters.user(OWNER_IDS))
async def ban_user_command(client, message):
    try:
        # Check if replying to a message or providing username/id
        if message.reply_to_message:
            target = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            input_arg = message.command[1]
            if input_arg.startswith('@'):
                # Username provided
                try:
                    user = await client.get_users(input_arg)
                    target = user.id
                except:
                    await message.reply_text("❌ User not found!")
                    return
            else:
                # Assume it's a user ID
                try:
                    target = int(input_arg)
                except ValueError:
                    await message.reply_text("❌ Invalid user ID format!")
                    return
        else:
            await message.reply_text("❌ Usage: /rmuser <username/id/reply>")
            return

        # Check if user exists in database
        user_data = await user_collection.find_one({"id": target})
        if not user_data:
            await message.reply_text("❌ User not found in database!")
            return

        # Confirmation message
        confirm_msg = (
            f"⚠️ **Permanent Ban Confirmation** ⚠️\n\n"
            f"User: `{target}`\n"
            f"Name: {user_data.get('name', 'Unknown')}\n"
            f"Characters: {len(user_data.get('characters', []))}\n\n"
            f"**This will:**\n"
            f"- Delete all their characters\n"
            f"- Add to banned list\n"
            f"- Prevent future collection"
        )

        # Confirmation buttons
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ CONFIRM BAN", callback_data=f"confirm_ban:{target}"),
                InlineKeyboardButton("❌ CANCEL", callback_data="cancel_ban")
            ]
        ])

        await message.reply_text(confirm_msg, reply_markup=keyboard)

    except Exception as e:
        print(f"Ban Error: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

@app.on_callback_query(filters.regex(r"^confirm_ban"))
async def confirm_ban_callback(client, callback_query):
    try:
        target = int(callback_query.data.split(':')[1])

        # Delete user's collection
        await user_collection.update_one(
            {"id": target},
            {"$set": {"characters": [], "favorites": []}}
        )

        # Add to banned list
        await banned_users.insert_one({
            "user_id": target,
            "banned_by": callback_query.from_user.id,
            "banned_at": datetime.datetime.now(),
            "is_banned": True
        })

        await callback_query.message.edit_text(
            f"🚫 User `{target}` has been permanently banned!\n"
            f"• Collection cleared\n"
            f"• Future collection disabled"
        )

    except Exception as e:
        print(f"Ban Confirm Error: {e}")
        await callback_query.message.edit_text("❌ Ban failed! Please check logs.")

@app.on_callback_query(filters.regex(r"^cancel_ban"))
async def cancel_ban_callback(client, callback_query):
    await callback_query.message.edit_text("✅ Ban cancelled. No changes were made.")

@app.on_message(filters.command("allowuser") & filters.user(OWNER_IDS))
async def unban_user_command(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ Usage: /allowuser <username/id>")
            return

        input_arg = message.command[1]
        if input_arg.startswith('@'):
            # Username provided
            try:
                user = await client.get_users(input_arg)
                target = user.id
            except:
                await message.reply_text("❌ User not found!")
                return
        else:
            # Assume it's a user ID
            try:
                target = int(input_arg)
            except ValueError:
                await message.reply_text("❌ Invalid user ID format!")
                return

        # Remove from banned list
        result = await banned_users.delete_one({"user_id": target})

        if result.deleted_count > 0:
            await message.reply_text(f"✅ User `{target}` has been unbanned and can collect again!")
        else:
            await message.reply_text(f"ℹ️ User `{target}` wasn't in the banned list.")

    except Exception as e:
        print(f"Unban Error: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

# Add this to your character collection handler to check bans
async def is_user_banned(user_id):
    banned = await banned_users.find_one({"user_id": user_id, "is_banned": True})
    return banned is not None

HELP_NAME = "Hᴀʀᴇᴍ"
HELP = """Use `/harem` or `/collection` to view your collected characters.

- Navigate pages using the buttons.
- Filter by rarity using the filter button.
- Use "Collection" button for detailed inline view.
- "💌 AMV" button shows a video-only collection.

Characters are grouped by anime and show the count you own."""
