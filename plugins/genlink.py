import re
import os
import json
import base64
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from config import ADMINS, LOG_CHANNEL, DB_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE
from plugins.users_api import get_user, get_short_link

# Users ki dynamic state track karne ke liye dictionaries
AWAITING_CONTENT = {}
BATCH_STATE = {}         
CUSTOM_BATCH_DATA = {}   

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

def get_share_button(link):
    share_text = "Get your files here! 👇"
    encoded_text = share_text.replace(" ", "%20")
    share_url = f"https://telegram.me/share/url?url={link}&text={encoded_text}"
    return InlineKeyboardMarkup([[InlineKeyboardButton("📤 SHARE URL 📤", url=share_url)]])

def get_custom_batch_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("PAUSE", callback_data="cb_pause")],
        [InlineKeyboardButton("GENERATE LINK", callback_data="cb_generate")],
        [InlineKeyboardButton("CANCEL BATCH", callback_data="cb_cancel")]
    ])

def extract_msg_info(message):
    LINK_REGEX = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
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


# ==================== INTERCEPT HANDLER ====================

@Client.on_message(filters.private & ~filters.command(["link", "batch", "custom_batch", "start", "api", "base_site"]) & filters.create(allowed), group=-1)
async def handle_conversations(bot, message):
    user_id = message.from_user.id
    username = (await bot.get_me()).username
    
    # ─── CASE A: CUSTOM ONE-BY-ONE BATCH ───
    if user_id in CUSTOM_BATCH_DATA:
        if message.text and message.text.startswith("/"):
            return
            
        try:
            if "control_messages" in CUSTOM_BATCH_DATA[user_id] and CUSTOM_BATCH_DATA[user_id]["control_messages"]:
                last_msg_obj = CUSTOM_BATCH_DATA[user_id]["control_messages"][-1]
                try: await last_msg_obj.delete()
                except: pass
            
            processing_msg = await message.reply_text("<b>PROCESSING... ⏳</b>")
            # 🌟 DB_CHANNEL me copy ho rha hai
            post = await message.copy(DB_CHANNEL)
            await processing_msg.delete()
            
            CUSTOM_BATCH_DATA[user_id]["msg_ids"].append(post.id)
            current_count = len(CUSTOM_BATCH_DATA[user_id]["msg_ids"])
            
            text = f"<b>Stored Message - {current_count}</b>\n\n<b>Want To Store More ? Just Send It Now.</b>"
            control_msg = await message.reply_text(text, reply_markup=get_custom_batch_panel())
            CUSTOM_BATCH_DATA[user_id]["control_messages"].append(control_msg)
            
        except Exception as e:
            await message.reply_text(f"❌ **Error while storing:** {str(e)}")
        message.stop_propagation()

    # ─── CASE B: SINGLE LINK WAITING STATE ───
    elif AWAITING_CONTENT.get(user_id):
        AWAITING_CONTENT[user_id] = False
        processing_msg = await message.reply_text("<b>PROCESSING... 🚀</b>")
        
        try:
            # 🌟 DB_CHANNEL me copy ho rha hai
            post = await message.copy(DB_CHANNEL)
            file_id = str(post.id)
            string = 'file_' + file_id
            outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
            
            user = await get_user(user_id)
            share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start={outstr}"
                
            if user["base_site"] and user["shortener_api"] != None:
                short_link = await get_short_link(user, share_link)
                response_text = f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>"
                await processing_msg.delete()
                await message.reply_text(response_text, reply_markup=get_share_button(short_link))
            else:
                response_text = f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>"
                await processing_msg.delete()
                await message.reply_text(response_text, reply_markup=get_share_button(share_link))
        except Exception as e:
            await processing_msg.edit(f"❌ **Error:** {str(e)}")
        message.stop_propagation()

    # ─── CASE C: CHANNEL BATCH ───
    elif user_id in BATCH_STATE:
        state = BATCH_STATE[user_id]
        if state["step"] == 1:
            chat_id, msg_id = extract_msg_info(message)
            if not chat_id or not msg_id:
                return await message.reply_text("❌ **Invalid Input!**")
            state["first_chat"] = chat_id
            state["first_msg"] = msg_id
            state["step"] = 2
            await message.reply_text(f"<b>Forward The Last Message From Your Batch Channel...</b>")
            message.stop_propagation()
            
        elif state["step"] == 2:
            chat_id, msg_id = extract_msg_info(message)
            if not chat_id or not msg_id:
                return await message.reply_text("❌ **Invalid Input!**")
            f_chat_id = state["first_chat"]
            f_msg_id = state["first_msg"]
            l_chat_id = chat_id
            l_msg_id = msg_id
            del BATCH_STATE[user_id]
            
            if f_chat_id != l_chat_id:
                return await message.reply_text("❌ **Chat IDs matched nahi hui!**")
                
            sts = await message.reply_text("**ɢᴇɴᴇʀᴀᴛɪɴɢ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ**...")
            outlist = []
            og_msg = 0
            
            async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
                if msg.empty or msg.service: continue
                file = {"channel_id": f_chat_id, "msg_id": msg.id}
                og_msg += 1
                outlist.append(file)
                
            file_name = f"batchmode_{user_id}.json"
            with open(file_name, "w+") as out:
                json.dump(outlist, out)
                
            # 🌟 DB_CHANNEL me Json file share ho rhi hai
            post = await bot.send_document(DB_CHANNEL, file_name, file_name="Batch.json", caption="⚠️ Batch Generated For Filestore.")
            os.remove(file_name)
            
            string = str(post.id)
            file_id = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
            user = await get_user(user_id)
            share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start=BATCH-{file_id}"
            
            if user["base_site"] and user["shortener_api"] != None:
                short_link = await get_short_link(user, share_link)
                await sts.edit(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>", reply_markup=get_share_button(short_link))
            else:
                await sts.edit(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>", reply_markup=get_share_button(share_link))
            message.stop_propagation()


# ==================== DIRECT MEDIA GENERATOR ====================

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    user_id = message.from_user.id
    if user_id in CUSTOM_BATCH_DATA: return
        
    username = (await bot.get_me()).username
    # 🌟 DB_CHANNEL me direct safe copy
    post = await message.copy(DB_CHANNEL)
    file_id = str(post.id)
    string = 'file_' + file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user = await get_user(user_id)
    share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start={outstr}"
    
    if user["base_site"] and user["shortener_api"] != None:
        short_link = await get_short_link(user, share_link)
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>", reply_markup=get_share_button(short_link))
    else:
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>", reply_markup=get_share_button(share_link))


# ==================== COMMAND HANDLERS ====================

@Client.on_message(filters.command(['link']) & filters.private & filters.create(allowed))
async def gen_link_s(bot, message):
    user_id = message.from_user.id
    AWAITING_CONTENT[user_id] = True
    await message.reply_text("<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>")

@Client.on_message(filters.command(['batch']) & filters.private & filters.create(allowed))
async def gen_link_batch(bot, message):
    user_id = message.from_user.id
    BATCH_STATE[user_id] = {"step": 1, "first_chat": None, "first_msg": None}
    await message.reply_text("<b>Forward The First Message From Your Batch Channel...</b>")

@Client.on_message(filters.command(['custom_batch']) & filters.private & filters.create(allowed))
async def start_custom_batch(bot, message):
    user_id = message.from_user.id
    CUSTOM_BATCH_DATA[user_id] = {"msg_ids": [], "control_messages": []}
    await message.reply('<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>')


# ==================== CALLBACK PANEL FOR CUSTOM BATCH ====================

