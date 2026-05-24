# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging, asyncio, os, re, random, pytz, aiohttp, requests, string, json, http.client, time
from datetime import date, datetime
from config import VERIFY_EXPIRE_TIME
from shortzy import Shortzy
from dbusers import db  # 🌟 NEW: Database settings load karne ke liye

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TOKENS = {}

async def get_verify_shorted_link(link):
    # 🌟 NEW: Render config ki jagah Database se live values uthayega
    settings = await db.get_settings()
    shortlink_url = settings.get("shortlink_url", "linkshortify.com")
    shortlink_api = settings.get("shortlink_api", "9d9199caec2c2e30e0670f1549ffa1a316caa541")

    if shortlink_url == "api.shareus.io":
        url = f'https://{shortlink_url}/easy_api'
        params = {
            "key": shortlink_api,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        try:
            shortzy = Shortzy(api_key=shortlink_api, base_site=shortlink_url)
            link = await shortzy.convert(link)
            return link
        except Exception as e:
            logger.error(f"Shortener Error: {e}")
            return link

async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if user.id in TOKENS.keys():
        TKN = TOKENS[user.id]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used == True:
                return False
            else:
                return True
    else:
        return False

async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    TOKENS[user.id] = {token: False}
    link = f"{link}verify-{user.id}-{token}"
    shortened_verify_url = await get_verify_shorted_link(link)
    return str(shortened_verify_url)

async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    TOKENS[user.id] = {token: True}
    
    # 🌟 UPDATED: Memory ki jagah user ka verification time MongoDB database me save hoga permanent
    current_time = int(time.time())
    await db.update_verify_time(user.id, current_time)

async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    
    # 🌟 NEW: Admin panel se check karega ki VERIFY_MODE On hai ya Off
    settings = await db.get_settings()
    if not settings.get("verify_mode", True):
        return True  # Agar Admin ne Verification Off kar rakhi hai, to user direct pass ho jayega

    # 🌟 UPDATED: Database se user ka last verified timestamp nikalenge
    last_verified = await db.get_verify_time(user.id)
    
    if last_verified == 0:
        return False # User ne kabhi verify nahi kiya
        
    # Ab check hoga ki token valid hai ya expire ho chuka hai
    if (int(time.time()) - last_verified) > VERIFY_EXPIRE_TIME:
        return False  # Verification Expire ho gaya
    else:
        return True   # Verification Valid hai
