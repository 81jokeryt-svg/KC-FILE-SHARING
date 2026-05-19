# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import os
import json
import base64
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE
from plugins.users_api import get_user, get_short_link

# Global dictionary to track active custom batches for users
CUSTOM_BATCH_DATA = {}

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

# Helper function for Custom Batch Inline Control Panel
def get_custom_batch_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("PAUSE", callback_data="cb_pause")],
        [InlineKeyboardButton("GENERATE LINK", callback_data="cb_generate")],
        [InlineKeyboardButton("CANCEL BATCH", callback_data="cb_cancel")]
    ])

# ==================== MESSAGE HANDLER (FOR MEDIA & CUSTOM BATCH) ====================

@Client.on_message(filters.private & filters.create(allowed))
async def handle_incoming_messages(bot, message):
    user_id = message.from_user.id
    username = (await bot.get_me()).username
    
    # 1. Check if user is currently creating a custom batch
    if user_id in CUSTOM_BATCH_DATA:
        if message.text and message.text.startswith("/"):
            return
            
        try:
            post = await message.copy(LOG_CHANNEL)
            CUSTOM_BATCH_DATA[user_id].append(post.id)
            
            msg_count = len(CUSTOM_BATCH_DATA[user_id])
            text = (
                f"<b>Stored Message - {msg_count}</b>\n\n"
                f"<b>Want To Store More ? Just Send It Now.</b>"
            )
            await message.reply(text, reply_markup=get_custom_batch_panel())
        except Exception as e:
            await message.reply(f"Error storing message: {e}")
        return

    # 2. Process as standard single file generation (Direct File Share)
    if message.document or message.video or message.audio:
        processing_msg = await message.reply("⏳ PROCESSING... 🚀")
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        string = 'file_' + file_id
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
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

# ==================== COMMAND 1: /link ====================

@Client.on_message(filters.command(['link']) & filters.create(allowed))
async def gen_link_s(bot, message):
    username = (await bot.get_me()).username
    replied = message.reply_to_message
    if not replied:
        return await message.reply('<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>')

    processing_msg = await message.reply("⏳ PROCESSING... 🚀")
    
    post = await replied.copy(LOG_CHANNEL)
    file_id = str(post.id)
    string = f"file_" + file_id
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

# ==================== COMMAND 2: /batch (CHANNEL TO CHANNEL BATCH) ====================

@Client.on_message(filters.command(['batch']) & filters.create(allowed))
async def gen_link_batch(bot, message):
    bot_info = await bot.get_me()
    username = bot_info.username
    
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
    
    sts = await message.reply("⏳ PROCESSING... 🚀")
    FRMT = "**ɢᴇɴᴇʀᴀᴛɪɴɢ ʟɪɴᴋ...**\n**ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs:** {total}\n**ᴅᴏɴᴇ:** {current}\n**ʀᴇᴍᴀɪɴɪɴɢ:** {rem}\n**sᴛᴀᴛᴜs:** {sts}"
    outlist = []

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
        og_msg += 1
        outlist.append(file)

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

# ==================== COMMAND 3: /custom_batch (USER-DRIVEN CUSTOM BATCH) ====================

@Client.on_message(filters.command(['custom_batch']) & filters.create(allowed))
async def start_custom_batch(bot, message):
    user_id = message.from_user.id
    CUSTOM_BATCH_DATA[user_id] = []
    await message.reply('<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>')

# ==================== CALLBACK QUERY HANDLER FOR CUSTOM BATCH PANELS ====================

@Client.on_callback_query(filters.regex(r"^cb_"))
async def handle_custom_batch_callbacks(bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    username = (await bot.get_me()).username
    
    if user_id not in CUSTOM_BATCH_DATA:
        return await callback_query.answer("No active batch session found. Start again with /custom_batch", show_alert=True)
        
    if data == "cb_pause":
        await callback_query.answer("Batch Paused. You can resume sending messages.", show_alert=True)
        
    elif data == "cb_cancel":
        CUSTOM_BATCH_DATA.pop(user_id, None)
        await callback_query.message.edit("<b>CANCELLED</b>")
        await callback_query.answer("Batch processing cancelled.")
        
    elif data == "cb_generate":
        msg_list = CUSTOM_BATCH_DATA.get(user_id, [])
        if not msg_list:
            return await callback_query.answer("You haven't stored any messages yet!", show_alert=True)
            
        await callback_query.answer("Generating link...")
        status_msg = await callback_query.message.edit("⚡ GENERATING LINK...... 🚀")
        
        outlist = []
        for msg_id in msg_list:
            outlist.append({
                "channel_id": LOG_CHANNEL,
                "msg_id": msg_id
            })
            
        file_path = f"batchmode_{user_id}.json"
        with open(file_path, "w+") as out:
            json.dump(outlist, out)
            
        post = await bot.send_document(LOG_CHANNEL, file_path, file_name="Batch.json", caption="⚠️ Custom Batch Generated.")
        if os.path.exists(file_path):
            os.remove(file_path)
            
        string = str(post.id)
        file_id = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        user = await get_user(user_id)
        
        if WEBSITE_URL_MODE == True:
            share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}"
        else:
            share_link = f"https://t.me/{username}?start=BATCH-{file_id}"
            
        CUSTOM_BATCH_DATA.pop(user_id, None)
        
        if user["base_site"] and user["shortener_api"] != None:
            short_link = await get_short_link(user, share_link)
            text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {short_link}</b>"
            await status_msg.edit(text, reply_markup=get_share_button(short_link))
        else:
            text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {share_link}</b>"
            await status_msg.edit(text, reply_markup=get_share_button(share_link))
