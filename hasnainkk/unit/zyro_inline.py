import re
from cachetools import TTLCache
from hasnainkk import user_collection, collection

# Caching to reduce database queries
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def get_user_collection(user_id):
    """ Get user collection from database """
    if user_id in user_collection_cache:
        return user_collection_cache[user_id]
    
    user = await user_collection.find_one({'id': int(user_id)})
    if user:
        user_collection_cache[user_id] = user
    return user

async def search_characters(query):
    """ Search characters based on name or anime """
    regex = re.compile(query, re.IGNORECASE)
    return await collection.find({"$or": [{"name": regex}, {"anime": regex}]}).to_list(length=None)

async def get_all_characters():
    """ Get all characters (cached for performance) """
    if 'all_characters' in all_characters_cache:
        return all_characters_cache['all_characters']

    characters = await collection.find({}).to_list(length=None)
    all_characters_cache['all_characters'] = characters
    return characters
