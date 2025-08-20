from hasnainkk import *
import importlib
import logging
from hasnainkk import ZYRO as app  # Pyrogram client
from hasnainkk.modules import ALL_MODULES
from telegram.ext import Application

# Logging setup
LOGGER = logging.getLogger(__name__)

# PTB Application setup
#application = Application.builder().token("YOUR_BOT_TOKEN").build()

def main() -> None:
    # Load all modules
    for module_name in ALL_MODULES:
        importlib.import_module(f"hasnainkk.modules.{module_name}")
    
    LOGGER.info("𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲🥳...")

    # Start both Pyrogram & PTB together
    try:
        app.start()  # Pyrogram
        LOGGER.info("Pyrogram client started successfully!")

        application.run_polling(drop_pending_updates=True)  # PTB
        LOGGER.info("PTB polling started successfully!")

    except Exception as e:
        LOGGER.error(f"Error while running bot: {e}")

    LOGGER.info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ☠︎︎MADE BY @hasnainkk on tg\n╚═════ஜ۩۞۩ஜ════╝"
    )

if __name__ == "__main__":
    main()
