import base64
import httpx
import os
from hasnainkk import BOT_USERNAME
from hasnainkk import ZYRO as app
from pyrogram import Client, filters
import pyrogram
from uuid import uuid4
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import aiofiles, aiohttp, requests

async def image_loader(image: str, link: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            if resp.status == 200:
                f = await aiofiles.open(image, mode="wb")
                await f.write(await resp.read())
                await f.close()
                return image
            return image

@app.on_message(filters.command("upscale", prefixes="/"))
async def upscale_image(client, message):
    chat_id = message.chat.id
    replied = message.reply_to_message
    if not replied:
        return await message.reply_text("Please Reply To An Image ...")
    if not replied.photo:
        return await message.reply_text("Please Reply To An Image ...")

    aux = await message.reply_text("Please Wait ...")
    image = await replied.download()

    try:
        response = requests.post(
            "https://api.deepai.org/api/torch-srgan",
            files={
                'image': open(image, 'rb'),
            },
            headers={'api-key': 'bf9ee957-9fad-46f5-a403-3e96ca9004e4'}
        )
        response.raise_for_status()

        data = response.json()
        image_link = data.get("output_url")

        if image_link:
            downloaded_image = await image_loader(image, image_link)
            await aux.delete()
            return await message.reply_document(downloaded_image)
        else:
            await aux.edit_text("Failed to get the output image link.")
    except requests.exceptions.RequestException as e:
        await aux.edit_text(f"Request failed: {str(e)}")
    except Exception as e:
        await aux.edit_text(f"An unexpected error occurred: {str(e)}")
    

