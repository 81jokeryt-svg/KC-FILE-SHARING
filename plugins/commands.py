# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import logging
import random
import asyncio
import time
from validators import domain
from Script import script
from plugins.dbusers import db
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token, generate_settings_keyboard 
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

# ⚙️ Helper function home page ko safe load karne ke liye
async def send_home_page(client, message):
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
    
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
        reply_markup=reply_markup
    )


# ==========================================
#            📡 HANDLERS PIPELINE
# ==========================================

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    username = client.me.username
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(user_id, message.from_user.mention))
    
    # 🌟 CENTRAL LOGIC: Ab database se user_id nahi, sidhe ADMIN ki setting load hogi global control ke liye
    user_settings = await db.get_user_settings(ADMIN)

    # Text arguments ko sahi tareeke se parse karenge taaki flow freeze na ho
    text_args = message.text.split(" ", 1) if message.text else []
    if len(text_args) < 2 or not text_args[1].strip():
        await send_home_page(client, message)
        return

    data = text_args[1].strip()
    
    # 1. HANDLE VERIFICATION LINKS
    if data.startswith("verify-"):
        try:
            parts = data.split("-")
            userid = parts[1]
            token = parts[2]
            original_file_payload = parts[3] if len(parts) > 3 else ""
        except IndexError:
            await message.reply_text(text="<b>Invalid link or Expired link ! Redirecting to Home...</b>", protect_content=True)
            await send_home_page(client, message)
            return

        if str(user_id) != str(userid):
            await message.reply_text(text="<b>Invalid link or Expired link ! Redirecting to Home...</b>", protect_content=True)
            await send_home_page(client, message)
            return
        
        if token == "DIRECT_TOKEN" or await check_token(client, userid, token):
            await verify_user(client, userid, token)
            await message.reply_text(
                text=script.VERIFIED_SUCCESS_TEXT.format(message.from_user.mention),
                protect_content=True
            )
            
            # 🌟 FIXED: String overwrite karke recursion chalayenge taaki flow na ruke
            if original_file_payload:
                message.text = f"/start {original_file_payload}"
                return await start(client, message)
            else:
                await send_home_page(client, message)
                return
        else:
            await message.reply_text(text="<b>Token Expired or Invalid! Redirecting to Home...</b>", protect_content=True)
            await send_home_page(client, message)
            return

    # 2. HANDLE BATCH LINKS
    elif data.startswith("BATCH-"):
        try:
            if user_settings.get("token_verification", VERIFY_MODE):
                if not await check_verification(client, user_id):
                    
                    if user_settings.get("link_shortener", False):
                        verify_url = await get_token(client, user_id, username, data)
                    else:
                        verify_url = f"https://telegram.me/{username}?start=verify-{user_id}-DIRECT_TOKEN-{data}"

                    not_verified_buttons = [
                        [InlineKeyboardButton("🚀 CLICK HERE TO VERIFY", url=verify_url)],
                        [InlineKeyboardButton("👑 BUY PREMIUM / PLANS", callback_data="open_premium_plans")],
                        [InlineKeyboardButton("❓ HOW TO VERIFY", url=VERIFY_TUTORIAL)]
                    ]
                    await message.reply_text(
                        text=script.NOT_VERIFIED_TEXT,
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup(not_verified_buttons)
                    )
                    return
        except Exception as e:
            await message.reply_text(f"**Verification Error - {e}. Redirecting...**")
            await send_home_page(client, message)
            return
            
        sts = await message.reply("<b>PLEASE WAIT... ⏳</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        
        if not msgs:
            try:
                decode_file_id = base64.urlsafe_b64decode(file_id + "=" * (-len(file_id) % 4)).decode("ascii")
                
                if "file_" in decode_file_id:
                    decode_file_id = decode_file_id.replace("file_", "")
                elif "_" in decode_file_id:
                    decode_file_id = decode_file_id.split("_", 1)[1]
                    
                msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
                file = await client.download_media(msg)
                
                with open(file, "r") as file_data:
                    msgs = json.loads(file_data.read())
                
                os.remove(file)
                BATCH_FILES[file_id] = msgs
            except Exception as e:
                await sts.edit("<b>FAILED TO FETCH BATCH DATA ❌</b>")
                await client.send_message(LOG_CHANNEL, f"UNABLE TO OPEN BATCH FILE: {str(e)}")
                await send_home_page(client, message)
                return
            
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
                    
                    if user_settings.get("custom_caption", True) and BATCH_FILE_CAPTION:
                        try:
                            f_caption = BATCH_FILE_CAPTION.format(file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                        except:
                            f_caption = f_caption
                    elif not user_settings.get("custom_caption", True):
                        f_caption = ""
                        
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
                    
                    is_protected = user_settings.get("protect_content", False)
                    msg_out = await info.copy(chat_id=message.from_user.id, caption=f_caption, protect_content=is_protected, reply_markup=reply_markup)
                else:
                    is_protected = user_settings.get("protect_content", False)
                    msg_out = await info.copy(chat_id=message.from_user.id, protect_content=is_protected)
                
                filesarr.append(msg_out)
                await asyncio.sleep(1)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                is_protected = user_settings.get("protect_content", False)
                msg_out = await info.copy(chat_id=message.from_user.id, protect_content=is_protected)
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
    else:
        if user_settings.get("token_verification", VERIFY_MODE):
            if not await check_verification(client, user_id):
                
                if user_settings.get("link_shortener", False):
                    verify_url = await get_token(client, user_id, username, data)
                else:
                    verify_url = f"https://telegram.me/{username}?start=verify-{user_id}-DIRECT_TOKEN-{data}"

                not_verified_buttons = [
                    [InlineKeyboardButton("🚀 CLICK HERE TO VERIFY", url=verify_url)],
                    [InlineKeyboardButton("👑 BUY PREMIUM / PLANS", callback_data="open_premium_plans")],
                    [InlineKeyboardButton("❓ HOW TO VERIFY", url=VERIFY_TUTORIAL)]
                ]
                await message.reply_text(
                    text=script.NOT_VERIFIED_TEXT,
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(not_verified_buttons)
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
                
                if user_settings.get("custom_caption", True) and CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                    except:
                        pass
                elif not user_settings.get("custom_caption", True):
                    f_caption = ""

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
                    
                is_protected = user_settings.get("protect_content", False)
                del_msg = await msg.copy(chat_id=message.from_user.id, caption=f_caption, reply_markup=reply_markup, protect_content=is_protected)
            else:
                is_protected = user_settings.get("protect_content", False)
                del_msg = await msg.copy(chat_id=message.from_user.id, protect_content=is_protected)
                
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
            await send_home_page(client, message)
            return

# ─── DIRECT /settings COMMAND HANDLER ───
# 🌟 FIXED: Sirf ADMIN hi global setting access kar sakta hai
@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client, message):
    user_id = message.from_user.id
    if user_id != ADMIN:
        return await message.reply_text("<b>❌ Error: Yeh command sirf bot admin use kar sakta hai!</b>")
        
    user_settings = await db.get_user_settings(ADMIN)
    
    text = (
        "╔════════════════════════╗\n"
        "🎬   **VENOM FILE STORE GLOBAL SETTINGS**\n"
        "╚════════════════════════╝\n\n"
        "⚙️ **WELCOME ADMIN!**\n"
        "Yahan se jo bhi toggle change karoge, wo poore bot ke sabhi users par apply hoga."
    )
    await message.reply_text(text, reply_markup=generate_settings_keyboard(user_settings))

# ─── DIRECT /plan COMMAND HANDLER ───
@Client.on_message(filters.command(['plan']) & filters.private)
async def premium_plan_cmd(bot, message):
    plan_buttons = [
        [
            InlineKeyboardButton("📸 Qr", callback_data="pay_via_qr"),
            InlineKeyboardButton("💳 Upi", callback_data="pay_via_upi")
        ],
        [
            InlineKeyboardButton("{ CLOSE }", callback_data="close_data")
        ]
    ]
    await message.reply_text(
        text=script.PREMIUM_PLAN_TEXT,
        protect_content=True,
        reply_markup=InlineKeyboardMarkup(plan_buttons)
    )


# ==========================================
#         📡 CALLBACKS EXECUTION HUB
# ==========================================

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id

    # 🌟 FIXED: Toggles ab hamesha ADMIN panel par target karenge
    if query.data.startswith("toggle_"):
        if user_id != ADMIN:
            return await query.answer("❌ Aap admin nahi ho! Yeh settings sirf admin badal sakta hai.", show_alert=True)
            
        setting_key = query.data.replace("toggle_", "")
        current_settings = await db.get_user_settings(ADMIN)
        
        new_value = not current_settings.get(setting_key, False)
        await db.update_user_setting(ADMIN, setting_key, new_value)
        current_settings[setting_key] = new_value
        
        status_str = "ENABLED ✅" if new_value else "DISABLED ❌"
        clean_name = setting_key.replace('_', ' ').title()
        await query.answer(f"{clean_name} is now {status_str}", show_alert=False)
        
        await query.message.edit_reply_markup(
            reply_markup=generate_settings_keyboard(current_settings)
        )
        return
        
    elif query.data == "open_premium_plans":
        await query.answer("Opening Premium Plans... 📥")
        plan_buttons = [
            [
                InlineKeyboardButton("📸 Qr", callback_data="pay_via_qr"),
                InlineKeyboardButton("💳 Upi", callback_data="pay_via_upi")
            ],
            [
                InlineKeyboardButton("{ CLOSE }", callback_data="close_data")
            ]
        ]
        await query.message.reply_text(
            text=script.PREMIUM_PLAN_TEXT,
            protect_content=True,
            reply_markup=InlineKeyboardMarkup(plan_buttons)
        )
        
    elif query.data == "pay_via_qr":
        await query.answer("Loading QR Code... 🖼️")
        qr_buttons = [
            [InlineKeyboardButton("📤 SEND PAYMENT SCREENSHOT", url="https://t.me/KingVJ01")],
            [InlineKeyboardButton("{ CLOSE }", callback_data="close_data")]
        ]
        await query.message.reply_photo(
            photo="https://i.ibb.co/PGbZztgZ/photo-2026-05-04-16-41-38-7636287934861148164.jpg", 
            caption=script.QR_REPLY_TEXT,
            reply_markup=InlineKeyboardMarkup(qr_buttons)
        )
        
    elif query.data == "pay_via_upi":
        await query.answer("Loading UPI Details... 💳")
        upi_buttons = [
            [InlineKeyboardButton("📤 SEND PAYMENT SCREENSHOT", url="https://t.me/KingVJ01")],
            [InlineKeyboardButton("{ CLOSE }", callback_data="close_data")]
        ]
        await query.message.reply_text(
            text=script.UPI_REPLY_TEXT,
            protect_content=True,
            reply_markup=InlineKeyboardMarkup(upi_buttons)
        )

    elif query.data == "close_data":
        await query.answer("Closed ❌")
        await query.message.delete()
        
    elif query.data == "about":
        await query.answer()
        buttons = [[
            InlineKeyboardButton('Hᴏᴍｅ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        try:
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
        except Exception as e:
            logger.error(f"Media edit error: {e}")

        reply_markup = InlineKeyboardMarkup(buttons)
        me2 = (await client.get_me()).mention
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(me2),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    # 🌟 CALLBACK HANDLER: `start` aur `back_to_main` dono par photo ke sath home page reset hoga
    elif query.data in ["start", "back_to_main"]:
        await query.answer()
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
        try:
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
        except Exception as e:
            logger.error(f"Media edit error: {e}")

        me2 = (await client.get_me()).mention
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, me2),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "clone":
        await query.answer()
        buttons = [[
            InlineKeyboardButton('Hᴏᴍｅ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        try:
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
        except Exception as e:
            logger.error(f"Media edit error: {e}")

    elif query.data == "help":
        await query.answer()
        buttons = [[
            InlineKeyboardButton('Hᴏᴍｅ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        try:
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
            )
        except Exception as e:
            logger.error(f"Media edit error: {e}")
            
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
