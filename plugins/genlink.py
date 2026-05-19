# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import os
import json
import base64
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE
from plugins.users_api import get_user, get_short_link

# Users ki dynamic state track karne ke liye dictionaries
AWAITING_CONTENT = {}
BATCH_STATE = {}         # Channel Batch: {user_id: {"step": 1, "first_chat": ..., "first_msg": ...}}
CUSTOM_BATCH_STATE = {}  # Custom Batch: {user_id: [msg_id1, msg_id2, ...]}

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

# Telegram link regex pattern
LINK_REGEX = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")

def extract_msg_info(message):
    """Message link ya forwarded message se chat_id aur msg_id nikalne ke liye helper function"""
    if message.text:
        match = LINK_REGEX.match(message.text.strip())
        if match:
            chat_id = match.group(4)
            msg_id = int(match.group(5))
            if chat_id.isnumeric():
                chat_id = int(("-100" + chat_id))
            return chat_id, msg_id
            
    if message.forward_from_chat:
        return message.forward_from_chat.id, message.forward_from_message_id
        
    return None, None

def get_custom_batch_keyboard():
    """Custom batch inline buttons"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏸️ PAUSE", callback_data="c_batch_pause")],
        [InlineKeyboardButton("🔗 GENERATE LINK", callback_data="c_batch_generate")],
        [InlineKeyboardButton("❌ CANCEL BATCH", callback_data="c_batch_cancel")]
    ])


# 🛠️ 1. INTERCEPT HANDLER (Sabhi states ko handle karne ke liye sabse upar)
@Client.on_message(filters.private & ~filters.command(["link", "batch", "custom_batch", "start", "api", "base_site"]) & filters.create(allowed), group=-1)
async def handle_conversations(bot, message):
    user_id = message.from_user.id
    username = (await bot.get_me()).username
    
    # ─── CASE A: SINGLE LINK WAITING STATE ───
    if AWAITING_CONTENT.get(user_id):
        AWAITING_CONTENT[user_id] = False
        processing_msg = await message.reply_text("<b>PROCESSING... 🚀</b>")
        
        try:
            post = await message.copy(LOG_CHANNEL)
            file_id = str(post.id)
            string = 'file_' + file_id
            outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
            
            user = await get_user(user_id)
            share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start={outstr}"
                
            if user["base_site"] and user["shortener_api"] != None:
                short_link = await get_short_link(user, share_link)
                response_text = f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>"
            else:
                response_text = f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>"
            
            await processing_msg.delete()
            await message.reply(response_text)
        except Exception as e:
            await processing_msg.edit(f"❌ **Error:** {str(e)}")
            
        message.stop_propagation()

    # ─── CASE B: BATCH LINK WAITING STATE (Channel Wise) ───
    elif user_id in BATCH_STATE:
        state = BATCH_STATE[user_id]
        
        if state["step"] == 1:
            chat_id, msg_id = extract_msg_info(message)
            if not chat_id or not msg_id:
                return await message.reply_text("❌ **Invalid Input!** Kripya forward tag ke sath message forward karein ya sahi link bhejen.")
                
            state["first_chat"] = chat_id
            state["first_msg"] = msg_id
            state["step"] = 2
            
            await message.reply_text(
                "<b>Forward The Last Message From Your Batch Channel (With Forward Tag)... Or Give Me Last Message Link From Your Batch Channel\n\n"
                f"NOTE : MAKE SURE THIS @{username} BOT IS ADMIN IN YOUR CHANNEL WITH FULL RIGHT</b>"
            )
            message.stop_propagation()
            
        elif state["step"] == 2:
            chat_id, msg_id = extract_msg_info(message)
            if not chat_id or not msg_id:
                return await message.reply_text("❌ **Invalid Input!** Kripya last message link ya forward tag ke sath message bhejen.")
                
            f_chat_id = state["first_chat"]
            f_msg_id = state["first_msg"]
            l_chat_id = chat_id
            l_msg_id = msg_id
            
            del BATCH_STATE[user_id]
            
            if f_chat_id != l_chat_id:
                return await message.reply_text("❌ **Chat IDs matched nahi hui!** Dono messages ek hi channel ke hone chahiye.")
                
            try:
                await bot.get_chat(f_chat_id)
            except ChannelInvalid:
                return await message.reply_text('❌ This may be a private channel / group. Make me an admin over there to index the files.')
            except Exception as e:
                return await message.reply_text(f'❌ Error: {e}')
                
            sts = await message.reply_text("**ɢᴇɴᴇʀᴀᴛɪɴɢ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ**.\n**ᴛʜɪs ᴍᴀʏ ᴛᴀᴋᴇ ᴛɪᴍᴇ ᴅᴇᴘᴇɴᴅɪɴɢ ᴜᴘᴏɴ ɴᴜᴍʙᴇʀ ᴏғ ᴍᴇssᴀɢᴇs**")
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
                file = {"channel_id": f_chat_id, "msg_id": msg.id}
                og_msg += 1
                outlist.append(file)
                
            file_name = f"batchmode_{user_id}.json"
            with open(file_name, "w+") as out:
                json.dump(outlist, out)
                
            post = await bot.send_document(LOG_CHANNEL, file_name, file_name="Batch.json", caption="⚠️ Batch Generated For Filestore.")
            os.remove(file_name)
            
            string = str(post.id)
            file_id = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
            
            user = await get_user(user_id)
            share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start=BATCH-{file_id}"
            
            if user["base_site"] and user["shortener_api"] != None:
                short_link = await get_short_link(user, share_link)
                await sts.edit(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\nContains `{og_msg}` files.\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>")
            else:
                await sts.edit(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\nContains `{og_msg}` files.\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")
                
            message.stop_propagation()

    # ─── CASE C: CUSTOM ONE-BY-ONE BATCH WAITING STATE ───
    elif user_id in CUSTOM_BATCH_STATE:
        try:
            processing_msg = await message.reply_text("<b>PROCESSING... ⏳</b>")
            post = await message.copy(LOG_CHANNEL)
            await processing_msg.delete()
            
            CUSTOM_BATCH_STATE[user_id].append(post.id)
            current_count = len(CUSTOM_BATCH_STATE[user_id])
            
            text = f"📦 **Stored Message - {current_count}**\n\nWant To Store More ? Just Send It Now."
            await message.reply_text(text, reply_markup=get_custom_batch_keyboard())
        except Exception as e:
            await message.reply_text(f"❌ **Error while storing:** {str(e)}")
            
        message.stop_propagation()


# 🛠️ 2. DIRECT MEDIA GENERATOR (Bina kisi command ke direct file aane par)
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    user_id = message.from_user.id
    
    # Agar user custom batch mode me hai, toh file ko batch me hi add karenge, direct single link nahi banayenge
    if user_id in CUSTOM_BATCH_STATE:
        return
        
    username = (await bot.get_me()).username
    post = await message.copy(LOG_CHANNEL)
    file_id = str(post.id)
    string = 'file_' + file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user = await get_user(user_id)
    share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start={outstr}"
    
    if user["base_site"] and user["shortener_api"] != None:
        short_link = await get_short_link(user, share_link)
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>")
    else:
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")


# 🛠️ 3. COMMAND HANDLER: /link
@Client.on_message(filters.command(['link']) & filters.private & filters.create(allowed))
async def gen_link_s(bot, message):
    user_id = message.from_user.id
    if user_id in BATCH_STATE: del BATCH_STATE[user_id]
    if user_id in CUSTOM_BATCH_STATE: del CUSTOM_BATCH_STATE[user_id]
    
    AWAITING_CONTENT[user_id] = True
    await message.reply_text("<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>")


# 🛠️ 4. COMMAND HANDLER: /batch (Channel wise sequential batch)
@Client.on_message(filters.command(['batch']) & filters.private & filters.create(allowed))
async def gen_link_batch(bot, message):
    user_id = message.from_user.id
    if user_id in AWAITING_CONTENT: AWAITING_CONTENT[user_id] = False
    if user_id in CUSTOM_BATCH_STATE: del CUSTOM_BATCH_STATE[user_id]
    
    username = (await bot.get_me()).username
    BATCH_STATE[user_id] = {"step": 1, "first_chat": None, "first_msg": None}
    
    await message.reply_text(
        "<b>Forward The First Message From Your Batch Channel (With Forward Tag)... Or Give Me First Message Link From Your Batch Channel\n\n"
        f"NOTE : MAKE SURE THIS @{username} BOT IS ADMIN IN YOUR CHANNEL WITH FULL RIGHT</b>"
    )


# 🛠️ 5. COMMAND HANDLER: /custom_batch (Dynamic single-single message batch)
@Client.on_message(filters.command(['custom_batch']) & filters.private & filters.create(allowed))
async def gen_custom_batch_start(bot, message):
    user_id = message.from_user.id
    if user_id in AWAITING_CONTENT: AWAITING_CONTENT[user_id] = False
    if user_id in BATCH_STATE: del BATCH_STATE[user_id]
    
    CUSTOM_BATCH_STATE[user_id] = []
    await message.reply_text("📥 **SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE**")


# 🛠️ 6. CALLBACK QUERY HANDLER FOR CUSTOM BATCH BUTTONS
@Client.on_callback_query(filters.regex("^c_batch_"))
async def handle_custom_batch_buttons(bot, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    username = (await bot.get_me()).username
    
    if user_id not in CUSTOM_BATCH_STATE:
        await callback_query.answer("Koi active batch session nahi mila.", show_alert=True)
        return

    if data == "c_batch_generate":
        msg_ids = CUSTOM_BATCH_STATE[user_id]
        if not msg_ids:
            await callback_query.answer("Pehle kuch messages toh bhejo!", show_alert=True)
            return
            
        await callback_query.message.edit_text("🚀 **GENERATING LINK...**")
        
        # LOG_CHANNEL ko dynamically handle karne ke liye format create karna
        outlist = []
        for m_id in msg_ids:
            outlist.append({"channel_id": LOG_CHANNEL, "msg_id": m_id})
            
        file_name = f"batchmode_{user_id}.json"
        with open(file_name, "w+") as out:
            json.dump(outlist, out)
            
        post = await bot.send_document(LOG_CHANNEL, file_name, file_name="Batch.json", caption="⚠️ Custom Batch Generated.")
        os.remove(file_name)
        
        del CUSTOM_BATCH_STATE[user_id]
        
        string = str(post.id)
        file_id = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        user = await get_user(user_id)
        share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start=BATCH-{file_id}"
        
        if user["base_site"] and user["shortener_api"] != None:
            short_link = await get_short_link(user, share_link)
            response_text = f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\nContains `{len(msg_ids)}` files.\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>"
        else:
            response_text = f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\nContains `{len(msg_ids)}` files.\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>"
            
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📤 SHARE URL", url=f"https://t.me/share/url?url={share_link}")]])
        await callback_query.message.edit_text(response_text, reply_markup=keyboard, disable_web_page_preview=True)

    elif data == "c_batch_cancel":
        del CUSTOM_BATCH_STATE[user_id]
        await callback_query.message.edit_text("❌ **Batch generation cancelled successfully.**")
        await callback_query.answer()
        
    elif data == "c_batch_pause":
        await callback_query.answer("Batch paused! Aap jab chahein tab messages bhej sakte hain.", show_alert=True)
