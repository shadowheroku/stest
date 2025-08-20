import logging
from os import execvp
from sys import executable
from traceback import format_exc
from hasnainkk import app
from pyrogram.types import Message

OWNER_IDS = [6138142369, 6346273488]  # Authorized owners


from pyrogram import filters

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.command("restart") & filters.user(OWNER_IDS))
async def restart_the_bot(c, m: Message):
    try:
        await m.reply_text("Restarting the bot...\nType `/ping` after a few moments.")
        execvp(executable, [executable, "-m", "hasnainkk"])
    except Exception as e:
        await m.reply_text(f"Failed to restart the bot due to:\n{e}")
        LOGGER.error(e)
        LOGGER.error(format_exc())
