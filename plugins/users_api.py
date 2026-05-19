# © Telegram : @KingVJ01 , GitHub : @VJBots
# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import aiohttp
import json
from plugins.clone import mongo_db

# ─── ASYNC SHORT LINK CONTROLLER ───
async def get_short_link(user, link):
    api_key = user["shortener_api"]
    base_site = user["base_site"]
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://{base_site}/api?api={api_key}&url={link}", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success" or "shortenedUrl" in data:
                        return data["shortenedUrl"]
    except Exception as e:
        print(f"Shortener Error: {e}")
        
    return link  # Fallback: Shortener fail hone par original link return karega

# ─── DATABASE USER FETCH (FIXED) ───
async def get_user(user_id):
    user_id = int(user_id)
    # PyMongo/Custom DB wrapper direct dictionary deta hai, isliye isse await nahi karte
    user = mongo_db.user.find_one({"user_id": user_id})
    
    if not user:
        res = {
            "user_id": user_id,
            "shortener_api": None,
            "base_site": None,
        }
        mongo_db.user.insert_one(res)
        user = mongo_db.user.find_one({"user_id": user_id})
        
    return user

# ─── DATABASE USER UPDATE (FIXED) ───
async def update_user_info(user_id, value: dict):
    user_id = int(user_id)
    myquery = {"user_id": user_id}
    newvalues = {"$set": value}
    mongo_db.user.update_one(myquery, newvalues)
