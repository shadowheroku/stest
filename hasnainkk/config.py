class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = 6138142369
    sudo_users = [5196578270, 6138142369, 6346273488, 6143079414, 6495101094]
    #", "6138142369", "6346273488", "6143079414", "6495101094",
    GROUP_ID  =  "-1002076327473"
    TOKEN = "6805432104:AAEAzB7wQvOJ09d3t9hl0XARCF6ZBI8LakU"
    mongo_url = "mongodb+srv://hasnainkk:hasnainkk@cluster0.mmvls.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://telegra.ph/file/62b70323bbbde7cf8ed4e.jpg", "https://telegra.ph/file/62b70323bbbde7cf8ed4e.jpg", "https://telegra.ph/file/192832f0e136f50193489.jpg", "https://telegra.ph/file/6f9e5e2112b633164a101.jpg", "https://telegra.ph/file/d84750e4a34801fc82114.jpg", "https://telegra.ph/file/87df160e3f499a9a18c8d.jpg"]
    SUPPORT_CHAT = "the_league_of_snatchers"
    UPDATE_CHAT = "MidexOzBotUpdates"
    BOT_USERNAME = "Snatch_Your_Character_Bot"
    CHARA_CHANNEL_ID = -1002572018720
    api_id = 24683098
    api_hash = "e4055cd239464e50e69bd73057c05dd3"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
