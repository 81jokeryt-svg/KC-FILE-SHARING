# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE
from plugins.users_api import get_user, get_short_link
import os
import json
import base64

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

# Helper function to create share button
def get_share_button(link):
    share_text = "Get your files here! 👇"
    encoded_text = share_text.replace(" ", "%20")
    share_url = f"https://telegram.me/share/url?url={link}&text={encoded_text}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 SHARE URL 📤", url=share_url)]
    ])

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

@Client.on_message((filters.document | filters.video | filters.audio) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    username = (await bot.get_me()).username
    
    processing_msg = await message.reply("⏳ PROCESSING... 🚀")
    
    file_type = message.media
    post = await message.copy(LOG_CHANNEL)
    file_id = str(post.id)
    string = 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if WEBSITE_URL_MODE == True:
        share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"
        
    if user["base_site"] and user["shortener_api"] != None:
        short_link = await get_short_link(user, share_link)
        text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {short_link}</b>"
        await processing_msg.edit(text, reply_markup=get_share_button(short_link))
    else:
        text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {share_link}</b>"
        await processing_msg.edit(text, reply_markup=get_share_button(share_link))
        

@Client.on_message(filters.command(['link']) & filters.create(allowed))
async def gen_link_s(bot, message):
    username = (await bot.get_me()).username
    replied = message.reply_to_message
    if not replied:
        return await message.reply('<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>')

    processing_msg = await message.reply("⏳ PROCESSING... 🚀")
    
    post = await replied.copy(LOG_CHANNEL)
    file_id = str(post.id)
    string = f"file_"
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if WEBSITE_URL_MODE == True:
        share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"
        
    if user["base_site"] and user["shortener_api"] != None:
        short_link = await get_short_link(user, share_link)
        text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {short_link}</b>"
        await processing_msg.edit(text, reply_markup=get_share_button(short_link))
    else:
        text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {share_link}</b>"
        await processing_msg.edit(text, reply_markup=get_share_button(share_link))
        

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

@Client.on_message(filters.command(['batch']) & filters.create(allowed))
async def gen_link_batch(bot, message):
    bot_info = await bot.get_me()
    username = bot_info.username
    
    # Automatic username logic for instruction message
    if " " not in message.text:
        return await message.reply(f"<b>Forward The First Message From Your Batch Channel (With Forward Tag) . Or Give Me First Message Link From Your Batch Channel\n\nNOTE : MAKE SURE THIS @{username} BOT IS ADMIN IN YOUR CHANNEL WITH FULL RIGHT</b>")
    
    links = message.text.strip().split(" ")
    if len(links) != 3:
        return await message.reply(f"<b>Forward The First Message From Your Batch Channel (With Forward Tag) . Or Give Me First Message Link From Your Batch Channel\n\nNOTE : MAKE SURE THIS @{username} BOT IS ADMIN IN YOUR CHANNEL WITH FULL RIGHT</b>")
    
    cmd, first, last = links
    regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
    match = regex.match(first)
    if not match:
        return await message.reply('Invalid link')
    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    if f_chat_id.isnumeric():
        f_chat_id = int(("-100" + f_chat_id))

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
    
    match = regex.match(last)
    if not match:
        return await message.reply('Invalid link')
    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))
    if l_chat_id.isnumeric():
        l_chat_id = int(("-100" + l_chat_id))

    if f_chat_id != l_chat_id:
        return await message.reply("Chat ids not matched.")
    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
    
    sts = await message.reply("⏳ PROCESSING... 🚀")

    FRMT = "**ɢᴇɴᴇʀᴀᴛɪɴɢ ʟɪɴᴋ...**\n**ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs:** {total}\n**ᴅᴏɴᴇ:** {current}\n**ʀᴇᴍᴀɪɴɪɴɢ:** {rem}\n**sᴛᴀᴛᴜs:** {sts}"

    outlist = []

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

    # file store without db channel
    og_msg = 0
    tot = 0
    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        tot += 1
        if og_msg % 20 == 0:
            try:
                await sts.edit(FRMT.format(total=l_msg_id-f_msg_id, current=tot, rem=((l_msg_id-f_msg_id) - tot), sts="Saving Messages"))
            except:
                pass
        if msg.empty or msg.service:
            continue
        file = {
            "channel_id": f_chat_id,
            "msg_id": msg.id
        }
        og_msg +=1
        outlist.append(file)

# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

    with open(f"batchmode_{message.from_user.id}.json", "w+") as out:
        json.dump(outlist, out)
    post = await bot.send_document(LOG_CHANNEL, f"batchmode_{message.from_user.id}.json", file_name="Batch.json", caption="⚠️ Batch Generated For Filestore.")
    os.remove(f"batchmode_{message.from_user.id}.json")
    string = str(post.id)
    file_id = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    if WEBSITE_URL_MODE == True:
        share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}"
    else:
        share_link = f"https://t.me/{username}?start=BATCH-{file_id}"
        
    if user["base_site"] and user["shortener_api"] != None:
        short_link = await get_short_link(user, share_link)
        text = f"<b>🎁 HERE IS YOUR BATCH LINK :\n\n📦 Total Files : {og_msg}\n\n⚠️ {short_link}</b>"
        await sts.edit(text, reply_markup=get_share_button(short_link))
    else:
        text = f"<b>🎁 HERE IS YOUR BATCH LINK :\n\n📦 Total Files : {og_msg}\n\n⚠️ {share_link}</b>"
        await sts.edit(text, reply_markup=get_share_button(share_link))
        
# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
