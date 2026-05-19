# © Telegram : @KingVJ01 , GitHub : @VJBots

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import aiohttp  # 🌟 NEW: Non-blocking async requests ke liye
import json
from motor.motor_asyncio import AsyncIOMotorClient
from plugins.clone import mongo_db

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

async def get_short_link(user, link):
    api_key = user["shortener_api"]
    base_site = user["base_site"]
    print(user)
    
    # 🌟 UPDATED: requests.get ko hata kar fully async aiohttp network call lagaya hai
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://{base_site}/api?api={api_key}&url={link}") as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "success" or "shortenedUrl" in data:
                    return data["shortenedUrl"]
    return link  # Fallback agar shortener fail ho jaye

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

async def get_user(user_id):
    user_id = int(user_id)
    # 🌟 UPDATED: Motor async calls me proper 'await' lagaya hai
    user = await mongo_db.user.find_one({"user_id": user_id})
    if not user:
        res = {
            "user_id": user_id,
            "shortener_api": None,
            "base_site": None,
        }
        await mongo_db.user.insert_one(res)
        user = await mongo_db.user.find_one({"user_id": user_id})
    return user

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

async def update_user_info(user_id, value:dict):
    user_id = int(user_id)
    myquery = {"user_id": user_id}
    newvalues = { "$set": value }
    # 🌟 UPDATED: Async database modifier call
    await mongo_db.user.update_one(myquery, newvalues)

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
