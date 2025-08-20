# ------------------------------ IMPORTS ---------------------------------
import logging
import os
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import filters as f
#from hasnainkk.config import Config as a
from pyrogram import Client

# --------------------------- LOGGING SETUP ------------------------------
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(),
    ],
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# ---------------------------- CONSTANTS ---------------------------------
api_id = 24683098
api_hash = "e4055cd239464e50e69bd73057c05dd3"

TOKEN = "7045334311:AAFXI_jTKzZP5bl0iEDYlWiQsjr8blGv6-A"
LOGGER_ID = -1002601918547
GROUP_ID = -1002601918547
CHARA_CHANNEL_ID = -1002601918547
#mongo_url = "mongodb+srv://herobh123456:hasnainkk07@hasnainkk07.uqjekii.mongodb.net/?retryWrites=true&w=majority"
PHOTO_URL = [
    "https://telegra.ph/file/62b70323bbbde7cf8ed4e.jpg",
    "https://telegra.ph/file/62b70323bbbde7cf8ed4e.jpg",
    "https://telegra.ph/file/192832f0e136f50193489.jpg",
    "https://telegra.ph/file/6f9e5e2112b633164a101.jpg",
    "https://telegra.ph/file/d84750e4a34801fc82114.jpg",
    "https://telegra.ph/file/87df160e3f499a9a18c8d.jpg"
]

SUPPORT_CHAT = "Midexoz_Support"
UPDATE_CHAT = "MidexOzBotUpdates"

BOT_USERNAME = "Snatch_Your_Character_Bot"

SUDO = [5196578270, 6138142369, 6346273488, 6346273488, 6143079414, 6495101094]
OWNER_ID = 6138142369
sudo_users = [5196578270, 6138142369, 6346273488, 6346273488, 6143079414, 6495101094]

BASE_API_URL = "mongodb+srv://hasnainkk:hasnainkk@cluster0.mmvls.mongodb.net/?retryWrites=true&w=majority"
mongo_url = BASE_API_URL
# --------------------- TELEGRAM BOT CONFIGURATION -----------------------
command_filter = f.create(lambda _, __, message: message.text and message.text.startswith("/"))

application = Application.builder().token(TOKEN).build()
ZYRO = Client("goku", api_id=api_id, api_hash=api_hash, bot_token=TOKEN)

# -------------------------- DATABASE SETUP ------------------------------
ddw = AsyncIOMotorClient(mongo_url)
db = ddw['Snatch']

# Collections
user_totals_collection = db['user_totals_lmaoooo']
group_user_totals_collection = db['group_user_totalsssssss']
top_global_groups_collection = db['top_global_groups']
pm_users = db['total_pm_users']
destination_collection = db['user_collection_lmaoooo']
destination_char = db['anime_characters_lol']


#db = lol['']

# -------------------------- GLOBAL VARIABLES ----------------------------
app = ZYRO
sudo_users = SUDO
collection = destination_char
user_collection = destination_collection
#--------------------------- STRIN ---------------------------------------

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
last_user = {}
warned_users = {}
user_cooldowns = {}

# -------------------------- POWER SETUP --------------------------------
from hasnainkk.unit.zyro_ban import *
from hasnainkk.unit.zyro_sudo import *
from hasnainkk.unit.zyro_react import *
from hasnainkk.unit.zyro_log import *
from hasnainkk.unit.zyro_send_img import *
from hasnainkk.unit.zyro_guess import *
from hasnainkk.unit.zyro_rarity import *
# ------------------------------------------------------------------------

# ---------------------------- END OF CODE ------------------------------
