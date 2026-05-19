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
from plugins.users_api import get_user, update_user_info
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
        return "Media File"
    chars = ["[", "]", "(", ")"]
    for c in chars:
        file_name = file_name.replace(c, "")
    file_name = '@VJ_Botz ' + ' '.join(filter(lambda x: not x.startswith('http') and not x.startswith('@') and not x.startswith('www.'), file_name.split()))
    return file_name

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
    
    # 1. HANDLE VERIFICATION LINKS
    if data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(text="<b>Invalid link or Expired link !</b>", protect_content=True)
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            await message.reply_text(
                text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all files till today midnight.</b>",
                protect_content=True
            )
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(text="<b>Invalid link or Expired link !</b>", protect_content=True)
        return

    # 2. HANDLE BATCH LINKS (Fully Fixed 🛠️)
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
            
        sts = await message.reply("<b>PLEASE WAIT... ⏳</b>") # Exact video matching text
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        
        if not msgs:
            try:
                # Padding automatic correct karke decode karega string ko
                decode_file_id = base64.urlsafe_b64decode(file_id + "=" * (-len(file_id) % 4)).decode("ascii")
                
                # Agar generator file ID string ke sath 'file_' bhej raha ho to use clean karein
                if "file_" in decode_file_id:
                    decode_file_id = decode_file_id.replace("file_", "")
                elif "_" in decode_file_id:
                    decode_file_id = decode_file_id.split("_", 1)[1]
                    
                msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
                
                # Log channel se direct json document file ko server par download karega
                file = await client.download_media(msg)
                
                with open(file, "r") as file_data:
                    msgs = json.loads(file_data.read())
                
                os.remove(file)
                BATCH_FILES[file_id] = msgs
            except Exception as e:
                await sts.edit("<b>FAILED TO FETCH BATCH DATA ❌</b>")
                return await client.send_message(LOG_CHANNEL, f"UNABLE TO OPEN BATCH FILE: {str(e)}")
            
        filesarr = []
        for msg_item in msgs:
            try:
                channel_id = int(msg_item.get("channel_id"))
                msgid = int(msg_item.get("msg_id"))
                info = await client.get_messages(channel_id, msgid)
                
                if info.empty or info.service:
                    continue
                    
                if info.media:
                    file_type = info.media
                    file = getattr(info, file_type.value)
                    f_caption = getattr(info, 'caption', '')
                    if f_caption:
                        f_caption = f"@VJ_Bots {f_caption.html}"
                    old_title = getattr(file, "file_name", "Media File")
                    title = formate_file_name(old_title)
                    
                    size = get_size(int(file.file_size)) if hasattr(file, "file_size") else "Unknown"
                    if BATCH_FILE_CAPTION:
                        try:
                            f_caption = BATCH_FILE_CAPTION.format(file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                        except:
                            f_caption = f_caption
                    if f_caption is None:
                        f_caption = f"@VJ_Bots {title}"
                        
                    if STREAM_MODE == True and (info.video or info.document):
                        stream = f"{URL}watch/{str(info.id)}/{quote_plus(get_name(info))}?hash={get_hash(info)}"
                        download = f"{URL}{str(info.id)}/{quote_plus(get_name(info))}?hash={get_hash(info)}"
                        button = [[
                            InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                            InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                        ],[
                            InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                        ]]
                        reply_markup = InlineKeyboardMarkup(button)
                    else:
                        reply_markup = None
                        
                    msg_out = await info.copy(chat_id=message.from_user.id, caption=f_caption, protect_content=False, reply_markup=reply_markup)
                else:
                    msg_out = await info.copy(chat_id=message.from_user.id, protect_content=False)
                
                filesarr.append(msg_out)
                await asyncio.sleep(1) # Floodwait se bachne ke liye interval delay
            except FloodWait as e:
                await asyncio.sleep(e.value)
                # Retry copy process post flood timeout window
                msg_out = await info.copy(chat_id=message.from_user.id, protect_content=False)
                filesarr.append(msg_out)
            except Exception as e:
                logger.error(f"Error copying batch sub-file: {e}")
                continue
                
        await sts.delete()
        
        if AUTO_DELETE_MODE == True:
            k = await client.send_message(chat_id=message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>")
            await asyncio.sleep(AUTO_DELETE_TIME)
            for x in filesarr:
                try:
                    await x.delete()
                except:
                    pass
            await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
        return

    # 3. HANDLE SINGLE FILE / PHOTO LINKS
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
        decoded_bytes = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        decoded_str = decoded_bytes.decode("ascii")
        
        if "file_" in decoded_str:
            decode_file_id = decoded_str.replace("file_", "")
        else:
            decode_file_id = decoded_str.split("_", 1)[1] if "_" in decoded_str else decoded_str
            
        msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
        
        if msg.media:
            media = getattr(msg, msg.media.value)
            old_title = media.file_name if hasattr(media, "file_name") else "Photo File"
            title = formate_file_name(old_title)
            size = get_size(media.file_size) if hasattr(media, "file_size") else "Unknown"
            
            f_caption = f"@VJ_Bots <code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
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
            await k.edit_text("<b>Your File/Video is successfully deleted!!!</b>")
        return
    except Exception as e:
        logger.error(f"Error in single file delivery: {str(e)}")
        pass

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
        if base_site == "None" or base_site == None:
            await update_user_info(user_id, {"base_site": None})
            return await m.reply("<b>Base Site updated successfully</b>")
            
        if not domain(base_site):
            return await m.reply(text=text, disable_web_page_preview=True)
        await update_user_info(user_id, {"base_site": base_site})
        await m.reply("<b>Base Site updated successfully</b>")

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
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
        me2 = (await client.get_me()).mention
        await query.message.edit_text(
            text=script.START_TXT.format(me2),
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
        me2 = (await client.get_me()).mention
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
