
import httpx
from pyrogram import Client, filters
import aiohttp
from hasnainkk import app 

DOWNLOADING_STICKER_ID = (
    "CAACAgEAAx0CfD7LAgACO7xmZzb83lrLUVhxtmUaanKe0_ionAAC-gADUSkNORIJSVEUKRrhHgQ"
)

@app.on_message(filters.regex(r"(https?://)?(www\.)?instagram\.com/[^ ]+"))
async def instadl_link_handler(client, message):
    downloading_sticker = await message.reply_sticker(DOWNLOADING_STICKER_ID)
    url = message.text.strip()
    
    # API endpoint with the URL
    api_url = f"https://missing-teressa-harsh098678-a9d3a3b3.koyeb.app/api/video?postUrl={url}"

    try:
        # Make the request to the API
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check the response status
                    if data["status"] == "success" and "videoUrl" in data["data"]:
                        video_url = data["data"]["videoUrl"]

                        why = f"Downloaded by {app.me.mention}"
                        
                        # Send the video to the user
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=video_url,
                            caption=why
                        )
                        await downloading_sticker.delete()
                    else:
                        await message.reply("❌ Failed to retrieve the video. Please try again later.")
                        await downloading_sticker.delete()
                else:
                    await message.reply("❌ Error: Unable to connect to the video API.")
                    await downloading_sticker.delete()
    except Exception as e:
        # Handle any unexpected errors
        await message.reply(f"❌ An error occurred: {str(e)}")
        await downloading_sticker.delete()
        
