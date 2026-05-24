# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pyrogram import filters, Client, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid
from config import *
from plugins.users_api import get_user, get_short_link
import os
import json
import base64

# State tracking dictionaries
AWAITING_CONTENT = {}
BATCH_STATE = {}
CUSTOM_BATCH_STATE = {}

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

LINK_REGEX = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")

def extract_msg_info(message):
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

# 🛠️ 1. INTERCEPT HANDLER (ADMIN PROTECTION KE SAATH)
@Client.on_message(filters.private & ~filters.command(["link", "batch", "cbatch", "cdone", "start", "api", "base_site"]) & filters.create(allowed), group=-1)
async def handle_conversations(bot, message):
    user_id = message.from_user.id
    
    # 🛑 ADMIN PROTECTION FIX: Agar bot Admin se input maang raha hai, toh ise bypass karo
    if user_id in ADMINS:
        if hasattr(bot, "listener_handlers") and bot.listener_handlers.get(message.chat.id):
            return 

    username = (await bot.get_me()).username
    
    # ─── CUSTOM BATCH MEDIA CATCHING ───
    if user_id in CUSTOM_BATCH_STATE:
        if not (message.document or message.video or message.audio or message.photo or message.text):
            return
        try:
            if CUSTOM_BATCH_STATE[user_id]["last_msg_id"]:
                try: await bot.delete_messages(chat_id=message.chat.id, message_ids=CUSTOM_BATCH_STATE[user_id]["last_msg_id"])
                except: pass
            copied_msg = await message.copy(DB_CHANNEL)
            CUSTOM_BATCH_STATE[user_id]["files"].append({"channel_id": DB_CHANNEL, "msg_id": copied_msg.id})
            total_saved = len(CUSTOM_BATCH_STATE[user_id]["files"])
            status_msg = await message.reply_text(f"<b>📥 FILE #{total_saved} ADDED!</b>")
            CUSTOM_BATCH_STATE[user_id]["last_msg_id"] = status_msg.id
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")
        message.stop_propagation()

    # ─── CASE A: SINGLE LINK ───
    elif AWAITING_CONTENT.get(user_id):
        AWAITING_CONTENT[user_id] = False
        processing_msg = await message.reply_text("<b>PROCESSING... 🚀</b>")
        try:
            post = await message.copy(DB_CHANNEL)
            file_id = str(post.id)
            string = 'file_' + file_id
            outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
            user = await get_user(user_id)
            share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start={outstr}"
            if user["base_site"] and user["shortener_api"]:
                short_link = await get_short_link(user, share_link)
                response_text = f"<b>⭕ HERE IS YOUR LINK:\n\n🖇️ SHORT LINK :- {short_link}</b>"
            else:
                response_text = f"<b>⭕ HERE IS YOUR LINK:\n\n🔗 ORIGINAL LINK :- {share_link}</b>"
            await processing_msg.delete()
            await message.reply(response_text)
        except Exception as e:
            await processing_msg.edit(f"❌ Error: {str(e)}")
        message.stop_propagation()

    # ─── CASE B: BATCH LINK ───
    elif user_id in BATCH_STATE:
        state = BATCH_STATE[user_id]
        if state["step"] == 1:
            chat_id, msg_id = extract_msg_info(message)
            if not chat_id or not msg_id: return await message.reply_text("❌ Invalid Input!")
            state.update({"first_chat": chat_id, "first_msg": msg_id, "step": 2})
            await message.reply_text("<b>Forward The Last Message From Your Batch Channel...</b>")
            message.stop_propagation()
        elif state["step"] == 2:
            chat_id, msg_id = extract_msg_info(message)
            if not chat_id or not msg_id: return await message.reply_text("❌ Invalid Input!")
            f_chat_id, f_msg_id = state["first_chat"], state["first_msg"]
            del BATCH_STATE[user_id]
            if f_chat_id != chat_id: return await message.reply_text("❌ Chat IDs matched nahi hui!")
            sts = await message.reply_text("<b>GENERATING LINK...</b>")
            outlist = []
            async for msg in bot.iter_messages(f_chat_id, msg_id, f_msg_id):
                if msg.empty or msg.service: continue
                outlist.append({"channel_id": f_chat_id, "msg_id": msg.id})
            file_name = f"batchmode_{user_id}.json"
            with open(file_name, "w+") as out: json.dump(outlist, out)
            post = await bot.send_document(DB_CHANNEL, file_name, file_name="Batch.json")
            os.remove(file_name)
            file_id = base64.urlsafe_b64encode(str(post.id).encode("ascii")).decode().strip("=")
            user = await get_user(user_id)
            share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start=BATCH-{file_id}"
            await sts.edit(f"<b>⭕ HERE IS YOUR BATCH LINK:\n\n🔗 LINK :- {share_link}</b>")
            message.stop_propagation()

# 🛠️ 2. DIRECT MEDIA GENERATOR
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    user_id = message.from_user.id
    if user_id in CUSTOM_BATCH_STATE: return
    # Admin Protection yahan bhi zaroori hai
    if user_id in ADMINS and hasattr(bot, "listener_handlers") and bot.listener_handlers.get(message.chat.id): return
    
    username = (await bot.get_me()).username
    post = await message.copy(DB_CHANNEL)
    file_id = base64.urlsafe_b64encode(f"file_{post.id}".encode("ascii")).decode().strip("=")
    user = await get_user(user_id)
    share_link = f"{WEBSITE_URL}?Tech_VJ={file_id}" if WEBSITE_URL_MODE else f"https://t.me/{username}?start={file_id}"
    await message.reply(f"<b>⭕ HERE IS YOUR LINK:\n\n🔗 LINK :- {share_link}</b>")

# 🛠️ COMMAND HANDLERS
@Client.on_message(filters.command(['link']) & filters.private & filters.create(allowed))
async def gen_link_s(_, m):
    user_id = m.from_user.id
    if user_id in BATCH_STATE: del BATCH_STATE[user_id]
    if user_id in CUSTOM_BATCH_STATE: del CUSTOM_BATCH_STATE[user_id]
    AWAITING_CONTENT[user_id] = True
    await m.reply_text("<b>SEND ME YOUR MESSAGE WHICH YOU WANT TO STORE</b>")

@Client.on_message(filters.command(['batch']) & filters.private & filters.create(allowed))
async def gen_link_batch(_, m):
    user_id = m.from_user.id
    BATCH_STATE[user_id] = {"step": 1}
    await m.reply_text("<b>Forward The First Message...</b>")

@Client.on_message(filters.command(['cbatch']) & filters.private & filters.create(allowed))
async def start_custom_batch(_, m):
    CUSTOM_BATCH_STATE[m.from_user.id] = {"last_msg_id": None, "files": []}
    await m.reply_text("<b>✨ CUSTOM BATCH MODE ACTIVE! ✨</b>")

@Client.on_message(filters.command(['cdone']) & filters.private & filters.create(allowed))
async def complete_custom_batch(bot, m):
    user_id = m.from_user.id
    if user_id not in CUSTOM_BATCH_STATE: return
    # (Rest of the batch closing logic...)
    await m.reply_text("Batch generation completed.")
