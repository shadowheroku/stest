import requests
from hasnainkk import TOKEN 

CHAT_ID = -1002003248653
BOT_USERNAME = "@Snatch\\_Your\\_Character\\_Bot"  # Escaped underscores for bot username
OWNER_NAME = "@hasnainkk"  # Escaped underscores for owner's username
IMAGE_URL = "https://files.catbox.moe/153qpp.jpg"

def send_start_message():
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    caption = """🤖 *Bot has started successfully\\!*\n\n
👤 *Bot:* {BOT_USERNAME}\n
🧑‍💻 *Owner:* {OWNER_NAME}\n\n
🚀 *Status:* All systems are operational\\!"""
    caption = caption.format(BOT_USERNAME=BOT_USERNAME, OWNER_NAME=OWNER_NAME)  # Format placeholders
    payload = {
        "chat_id": CHAT_ID,
        "photo": IMAGE_URL,
        "caption": caption,
        "parse_mode": "MarkdownV2"  # Use MarkdownV2 for proper escaping
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        print("Start message sent successfully.")
    except requests.exceptions.RequestException as e:
        if response is not None:
            print(f"Error response: {response.text}")
        print(f"Failed to send start message: {e}")
