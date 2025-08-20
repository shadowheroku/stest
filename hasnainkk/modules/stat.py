from pyrogram import Client, filters, enums
from hasnainkk import ZYRO as app, user_collection, collection, RARITY_NAMES
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

async def create_info_image(profile_photo_url, user_id):
    template_path = os.path.join("hasnainkk", "imgs", "userinfo.png")
    if os.path.exists(template_path):
        template_img = Image.open(template_path)
    else:
        template_response = requests.get("https://files.catbox.moe/0r2z2d.png")
        template_img = Image.open(BytesIO(template_response.content))
    
    try:
        response = requests.get(profile_photo_url)
        profile_img = Image.open(BytesIO(response.content))
    except:
        profile_img = Image.new('RGB', (200, 200), 'black')
    
    profile_img = profile_img.resize((400, 400))
    mask = Image.new('L', profile_img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 400, 400), fill=255)
    output = Image.new('RGBA', profile_img.size, (0, 0, 0, 0))
    output.paste(profile_img, (0, 0))
    output.putalpha(mask)
    x = (template_img.width - output.width) // 2
    y = (template_img.height - output.height) // 2
    template_img.paste(output, (x, y), output)
    
    draw = ImageDraw.Draw(template_img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text = f"ID: {user_id}"
    text_width = draw.textlength(text, font=font)
    x_text = (template_img.width - text_width) // 2
    draw.text((x_text, 600), text, font=font, fill='white')
    
    bio = BytesIO()
    bio.name = 'user_info.png'
    template_img.save(bio, 'PNG')
    bio.seek(0)
    return bio

@app.on_message(filters.command(["stat", "profile"]))
async def info(client, message):
    replymsg = await message.reply_text("<b><i>Fetching Your Profile...</i></b>", quote=True)
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    try:
        photos = await client.get_profile_photos(user_id, limit=1)
        if photos:
            photo = await client.download_media(photos[0].file_id, in_memory=True)
            photo_url = BytesIO(photo.getvalue())
        else:
            photo_url = "https://files.catbox.moe/ckecty.jpg"
    except:
        photo_url = "https://files.catbox.moe/ckecty.jpg"

    info_image = await create_info_image(photo_url, user_id)
    user = await user_collection.find_one({'id': user_id}, {'characters': 1})
    
    if not user:
        await replymsg.edit_text("You do not have any characters yet.")
        return

    characters = user.get('characters', [])
    total_waifus = len(characters)
    total_characters_in_bot = await collection.count_documents({})
    harem_percentage = (total_waifus / total_characters_in_bot) * 100 if total_characters_in_bot > 0 else 0

    characters_per_segment = 1000
    development_bar_filled = min(total_waifus // characters_per_segment, 10)
    development_bar = '▰' * development_bar_filled + '▱' * (10 - development_bar_filled)

    rarity_counts = {}
    for char in characters:
        rarity = char.get("rarity", "Unknown")
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

    rarity_text = "\n".join([f"├─➩ {rarity}: {count}" for rarity, count in rarity_counts.items()])

    all_users = await user_collection.find({}, {'id': 1, 'characters': 1}).to_list(None)
    user_waifus_count = [(user.get('id', 'Unknown'), len(user.get('characters', []))) for user in all_users]
    sorted_users = sorted(user_waifus_count, key=lambda x: x[1], reverse=True)
    global_rank = next((index + 1 for index, (uid, count) in enumerate(sorted_users) if uid == user_id), "Not Available")

    info_message = f"""╭──「 🎗️ Gᴀᴍɪɴɢ ᴘʀᴏғɪʟᴇ 」
├─➩ 👤 ᴜsᴇʀ: {first_name}
├─➩ 🔩 ᴜsᴇʀ ɪᴅ: {user_id}
├─➩ ⚡ ᴛᴏᴛᴀʟ ᴄʜᴀʀᴀᴄᴛᴇʀ: {total_waifus} ({total_waifus})
├─➩ 🫧 ʜᴀʀᴇᴍ: {total_waifus}/{total_characters_in_bot} ({harem_percentage:.3f}%)
├─➩ 📈 ᴘʀᴏɢʀᴇss ʙᴀʀ:
╰         {development_bar}

╭───────────────────
{rarity_text}
╰───────────────────

╭───────────────────
├─➩ 🌍 ɢʟᴏʙᴀʟ ᴘᴏsɪᴛɪᴏɴ: {global_rank}
╰───────────────────"""
    
    await replymsg.delete()
    await message.reply_photo(photo=info_image, caption=info_message, parse_mode=enums.ParseMode.HTML)
    
