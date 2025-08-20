from pyrogram import Client, filters
import os
from PIL import Image
import shutil
from hasnainkk import ZYRO as app


# Path for storing downloaded files
DOWNLOAD_PATH = "downloads/"

# Ensure the downloads directory exists
os.makedirs(DOWNLOAD_PATH, exist_ok=True)


@app.on_message(filters.command("getsticker") & filters.reply, group=99828197)
def get_sticker_as_image(client, message):
    if message.reply_to_message.sticker:
        sticker = message.reply_to_message.sticker

        # Download the sticker
        file_path = app.download_media(sticker.file_id, DOWNLOAD_PATH)
        
        if sticker.is_animated:
            message.reply_text("This is an animated sticker. Cannot convert to an image.")
            return

        # Convert webp to png
        if file_path.endswith(".webp"):
            image = Image.open(file_path).convert("RGBA")
            output_path = file_path.replace(".webp", ".png")
            image.save(output_path, "PNG")
            os.remove(file_path)  # Remove the original webp file
            file_path = output_path

        # Send the image back
        message.reply_photo(photo=file_path)

        # Clean up the file after sending
        os.remove(file_path)
    else:
        message.reply_text("Please reply to a sticker with /getsticker to convert it to an image.")

@app.on_message(filters.command("getvideosticker") & filters.reply, group=99917176)
def get_video_sticker(client, message):
    if message.reply_to_message.sticker:
        sticker = message.reply_to_message.sticker

        if not sticker.is_video:
            message.reply_text("This is not a video sticker. Please reply to a video sticker.")
            return

        # Download the video sticker
        file_path = app.download_media(sticker.file_id, DOWNLOAD_PATH)

        # Ensure it is saved as .mp4
        video_path = file_path.replace(".webm", ".mp4") if file_path.endswith(".webm") else file_path
        if video_path != file_path:
            shutil.move(file_path, video_path)

        # Send the video back
        message.reply_video(video=video_path)

        # Clean up the file after sending
        os.remove(video_path)
    else:
        message.reply_text("Please reply to a video sticker with /getvideosticker to convert it to a video.")

@app.on_message(filters.command(["getsticker", "getvideosticker"]), group=9998997)
def handle_no_reply(client, message):
    if not message.reply_to_message:
        message.reply_text("Please reply to a sticker and then use the command.")

