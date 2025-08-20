# (©) Anonymous Emperor 

from pyrogram import enums, filters
from pyrogram.types import Message

from hasnainkk import ZYRO as app
from database.users_db import Users
from database.chats_db import Chats
#from hasnainkk.config import Config as a
from hasnainkk import SUDO as OWNER_ID


@app.on_message(filters.command(["stats"]), group=969726)
async def get_stats(_, m: Message):
    if m.from_user.id not in OWNER_ID:
        return

    userdb = Users
    chatdb = Chats

    replymsg = await m.reply_text("<b><i>Fetching Stats...</i></b>", quote=True)
    rply = (
        "📊 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦 📊\n\n"
        "<b>Here are the statistics of the bot:</b>\n\n"
        f"<b>👥 Users:</b> <code>{(userdb.count_users())}</code>\n"
        f"<b>💬 Chats:</b> <code>{(chatdb.count_chats())}</code>\n\n"
        "<a href='https://t.me/MidexOzBotUpdates'>𝙐𝙋𝘿𝘼𝙏𝙀𝙎</a> | "
        "<a href='https://t.me/Midexoz_Support'>𝙎𝙐𝙋𝙋𝙊𝙍𝙏</a>\n\n"
        f"「 𝙈𝘼𝘿𝙀 𝘽𝙔 <a href='t.me/LordIzana'>𝗜𝒵𝗔𝗡𝗔</a> 」\n"
    )
    await replymsg.edit_text(
        rply, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True
    )
    return
