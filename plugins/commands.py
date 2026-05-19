# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import logging
import random
import asyncio
from validators import domain
from Script import script
from plugins.dbusers import db
from pyrogram import Client, filters, enums
from plugins.users_api import get_user, update_user_info, get_short_link
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token
from config import *
import re
import json
import base64
from urllib.parse import quote_plus
from TechVJ.utils.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}
# Global dictionary to track active custom batches for users
CUSTOM_BATCH_DATA = {}

# Helper function to check if user has access
async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

def get_size(size):
    """Get size in readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def formate_file_name(file_name):
    if not file_name:
        return "Unknown_File"
    chars = ["[", "]", "(", ")"]
    for c in chars:
        file_name = file_name.replace(c, "")
    file_name = '@VJ_Botz ' + ' '.join(filter(lambda x: not x.startswith('http') and not x.startswith('@') and not x.startswith('www.'), file_name.split()))
    return file_name

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

# ==================== INTERCEPTOR HANDLER FOR PRIVATE MESSAGES & CUSTOM BATCH ====================

@Client.on_message(filters.private & filters.incoming & ~filters.command(["start", "api", "base_site", "custom_batch", "link", "batch"]))
async def handle_incoming_private_messages(client, message):
    user_id = message.from_user.id
    username = client.me.username
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
        
    # 1. If user is in active custom batch creation loop
    if user_id in CUSTOM_BATCH_DATA:
        try:
            post = await message.copy(LOG_CHANNEL)
            CUSTOM_BATCH_DATA[user_id].append(post.id)
            
            msg_count = len(CUSTOM_BATCH_DATA[user_id])
            text = (
                f"<b>Stored Message - {msg_count}</b>\n\n"
                f"<b>Want To Store More ? Just Send It Now.</b>"
            )
            await message.reply_text(text, reply_markup=get_custom_batch_panel())
        except Exception as e:
            await message.reply_text(f"Error storing message: {e}")
        return

    # 2. Universal Handler (Ab Text/Photo bhejoge toh direct link automatic generate karega)
    processing_msg = await message.reply_text("⏳ PROCESSING... 🚀")
    try:
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        string = 'file_' + file_id
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        user = await get_user(user_id)
        
        if WEBSITE_URL_MODE == True:
            share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
        else:
            share_link = f"https://t.me/{username}?start={outstr}"
            
        if user and user.get("base_site") and user.get("shortener_api") is not None:
            short_link = await get_short_link(user, share_link)
            text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {short_link}</b>"
            await processing_msg.edit_text(text, reply_markup=get_share_button(short_link))
        else:
            text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {share_link}</b>"
            await processing_msg.edit_text(text, reply_markup=get_share_button(share_link))
    except Exception as e:
        await processing_msg.edit_text(f"<b>Error processing message: {e}</b>")

# ==================== COMMANDS REGISTRATION ====================

@Client.on_message(filters.command("custom_batch") & filters.private)
async def start_custom_batch(client, message):
    user_id = message.from_user.id
    CUSTOM_BATCH_DATA[user_id] = []
    await message.reply_text('<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>')

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    username = client.me.username
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
            ],[
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_bots')
            ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ]]
        if CLONE_MODE == True:
            buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
        reply_markup = InlineKeyboardMarkup(buttons)
        me = client.me
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, me.mention),
            reply_markup=reply_markup
        )
        return
    
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
        
    if data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            await message.reply_text(
                text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all files till today midnight.</b>",
                protect_content=True
            )
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
            
    elif data.split("-", 1)[0] == "BATCH":
        try:
            if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
                btn = [[
                    InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
                ],[
                    InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
                ]]
                await message.reply_text(
                    text="<b>You are not verified !\nKindly verify to continue !</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
        except Exception as e:
            return await message.reply_text(f"**Error - {e}**")
            
        sts = await message.reply("**🔺 ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            decode_file_id = base64.urlsafe_b64decode(file_id + "=" * (-len(file_id) % 4)).decode("ascii")
            msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
            media = getattr(msg, msg.media.value if msg.media else "", None)
            
            if media:
                file_to_download = media.file_id
            else:
                file_to_download = msg.document.file_id
                
            file = await client.download_media(file_to_download)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except Exception as e:
                await sts.edit(f"FAILED: {e}")
                return await client.send_message(LOG_CHANNEL, f"UNABLE TO OPEN FILE: {e}")
            if os.path.exists(file):
                os.remove(file)
            BATCH_FILES[file_id] = msgs
            
        filesarr = []
        for msg in msgs:
            channel_id = int(msg.get("channel_id"))
            msgid = msg.get("msg_id")
            info = await client.get_messages(channel_id, int(msgid))
            
            if info.media:
                file_type = info.media
                file = getattr(info, file_type.value, None)
                f_caption = getattr(info, 'caption', '')
                if f_caption:
                    f_caption = f"@VJ_Bots {f_caption.html}"
                
                old_title = getattr(file, "file_name", "Photo/Media") if file else "Photo/Media"
                title = formate_file_name(old_title)
                size = get_size(int(file.file_size)) if file and hasattr(file, 'file_size') else "0 Bytes"
                
                if BATCH_FILE_CAPTION and file:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except:
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"@VJ_Bots {title}"
                    
                if STREAM_MODE == True and (info.video or info.document):
                    log_msg = info
                    stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    button = [[
                        InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                        InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                    ],[
                        InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                    ]]
                    reply_markup=InlineKeyboardMarkup(button)
                else:
                    reply_markup = None
                    
                try:
                    copied_msg = await info.copy(chat_id=message.from_user.id, caption=f_caption, protect_content=False, reply_markup=reply_markup)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    copied_msg = await info.copy(chat_id=message.from_user.id, caption=f_caption, protect_content=False, reply_markup=reply_markup)
                except Exception as e:
                    logger.error(f"Failed to copy media in batch: {e}")
                    continue
            else:
                try:
                    copied_msg = await info.copy(chat_id=message.from_user.id, protect_content=False)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    copied_msg = await info.copy(chat_id=message.from_user.id, protect_content=False)
                except Exception as e:
                    logger.error(f"Failed to copy text in batch: {e}")
                    continue
                    
            filesarr.append(copied_msg)
            await asyncio.sleep(1) 
            
        await sts.delete()
        if AUTO_DELETE_MODE == True:
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>")
            await asyncio.sleep(AUTO_DELETE_TIME)
            for x in filesarr:
                try:
                    await x.delete()
                except:
                    pass
            try:
                await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
            except:
                pass
        return

    try:
        real_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
        if "_" in real_data:
            pre, decode_file_id = real_data.split("_", 1)
        else:
            decode_file_id = real_data
    except:
        decode_file_id = data

    if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
        btn = [[
            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
        ],[
            InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
        ]]
        await message.reply_text(
            text="<b>You are not verified !\nKindly verify to continue !</b>",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
        
    try:
        msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
        if msg.media:
            media = getattr(msg, msg.media.value, None)
            old_title = getattr(media, "file_name", "Photo/Media") if media else "Photo/Media"
            title = formate_file_name(old_title)
            size = get_size(media.file_size) if media and hasattr(media, 'file_size') else "0 Bytes"
            
            f_caption = f"@VJ_Bots <code>{title}</code>"
            if CUSTOM_FILE_CAPTION and media:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    pass
                    
            if STREAM_MODE == True and (msg.video or msg.document):
                log_msg = msg
                stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                button = [[
                    InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                    InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                ],[
                    InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                ]]
                reply_markup=InlineKeyboardMarkup(button)
            else:
                reply_markup = None
                
            del_msg = await msg.copy(chat_id=message.from_user.id, caption=f_caption, reply_markup=reply_markup, protect_content=False)
        else:
            del_msg = await msg.copy(chat_id=message.from_user.id, protect_content=False)
            
        if AUTO_DELETE_MODE == True:
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>")
            await asyncio.sleep(AUTO_DELETE_TIME)
            try:
                await del_msg.delete()
            except:
                pass
            try:
                await k.edit_text("<b>Your File/Video is successfully deleted!!!</b>")
            except:
                pass
        return
    except Exception as e:
        logger.error(f"Error extracting single file/text: {e}")
        await message.reply_text("<b>Error: Unable to fetch this message/file.</b>")

@Client.on_message(filters.command('api') & filters.private)
async def shortener_api_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command

    if len(cmd) == 1:
        s = script.SHORTENER_API_MESSAGE.format(base_site=user["base_site"], shortener_api=user["shortener_api"])
        return await m.reply(s)

    elif len(cmd) == 2:    
        api = cmd[1].strip()
        await update_user_info(user_id, {"shortener_api": api})
        await m.reply("<b>Shortener API updated successfully to</b> " + api)

@Client.on_message(filters.command("base_site") & filters.private)
async def base_site_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command
    text = f"`/base_site (base_site)`\n\n<b>Current base site: None\n\n EX:</b> `/base_site shortnerdomain.com`\n\nIf You Want To Remove Base Site Then Copy This And Send To Bot - `/base_site None`"
    if len(cmd) == 1:
        return await m.reply(text=text, disable_web_page_preview=True)
    elif len(cmd) == 2:
        base_site = cmd[1].strip()
        if base_site.lower() == "none":
            await update_user_info(user_id, {"base_site": None})
            return await m.reply("<b>Base Site removed successfully</b>")
            
        if not domain(base_site):
            return await m.reply(text=text, disable_web_page_preview=True)
        await update_user_info(user_id, {"base_site": base_site})
        await m.reply("<b>Base Site updated successfully</b>")

# ==================== CALLBACKS (INCLUDING CUSTOM BATCH PACK) ====================

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    username = client.me.username
    
    # Custom Batch Inline Actions Processing
    if data.startswith("cb_"):
        if user_id not in CUSTOM_BATCH_DATA:
            return await query.answer("No active batch session found. Start again with /custom_batch", show_alert=True)
            
        if data == "cb_pause":
            await query.answer("Batch Paused. You can resume sending messages.", show_alert=True)
            
        elif data == "cb_cancel":
            CUSTOM_BATCH_DATA.pop(user_id, None)
            await query.message.edit_text("<b>CANCELLED</b>")
            await query.answer("Batch processing cancelled.")
            
        elif data == "cb_generate":
            msg_list = CUSTOM_BATCH_DATA.get(user_id, [])
            if not msg_list:
                return await query.answer("You haven't stored any messages yet!", show_alert=True)
                
            await query.answer("Generating link...")
            status_msg = await query.message.edit_text("⚡ GENERATING LINK...... 🚀")
            
            outlist = []
            for msg_id in msg_list:
                outlist.append({
                    "channel_id": LOG_CHANNEL,
                    "msg_id": msg_id
                })
                
            file_path = f"batchmode_{user_id}.json"
            with open(file_path, "w+") as out:
                json.dump(outlist, out)
                
            post = await client.send_document(LOG_CHANNEL, file_path, file_name="Batch.json", caption="⚠️ Custom Batch Generated.")
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
            
            if user and user.get("base_site") and user.get("shortener_api") is not None:
                short_link = await get_short_link(user, share_link)
                text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {short_link}</b>"
                await status_msg.edit_text(text, reply_markup=get_share_button(short_link))
            else:
                text = f"<b>🎁 HERE IS YOUR LINK :\n\n⚠️ {share_link}</b>"
                await status_msg.edit_text(text, reply_markup=get_share_button(share_link))
        return

    # Standard Button Callbacks
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        me2 = client.me.mention
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(me2),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
        ],[
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_bots')
        ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ]]
        if CLONE_MODE == True:
            buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        me2 = client.me.mention
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, me2),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "clone":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CLONE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )          
    
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
