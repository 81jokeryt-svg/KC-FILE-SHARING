# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import uuid
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.dbusers import db  # Database wrapper matching motor driver
import config

# Admin panel state tracking session memory map
ADMIN_MGMT_STATES = {}

# ==========================================
# --- 1. REMOVE USER (SECURE DELETE) ---
# ==========================================
@Client.on_message(filters.command("remove") & filters.private & filters.incoming)
async def remove_user_start(client, message):
    if message.from_user.id != config.ADMIN_ID: 
        return
        
    ADMIN_MGMT_STATES[message.from_user.id] = {"step": "awaiting_remove_id"}
    await message.reply_text(
        "👤 <b>User ko remove karein:</b>\n\nUs user ki <b>ID</b> bhejein jiska access khatam karna hai (ya /cancel):", 
        parse_mode=enums.ParseMode.HTML
    )


# ==========================================
# --- 2. MANAGE CHANNELS & STORIES ---
# ==========================================
@Client.on_message(filters.command("channels") & filters.private & filters.incoming)
async def list_channels(client, message):
    if message.from_user.id != config.ADMIN_ID: 
        return

    # Direct fetching all entry objects from active connection pipeline
    cursor = db.db.channels_col.find()
    # Loading list into memory safely using async loop layout
    all_items = await cursor.to_list(length=200)
    
    keyboard_buttons = []
    for ch in all_items:
        raw_name = ch.get('name') or "Unnamed Item"
        # Strict first line display logic inside dashboard view
        clean_name = raw_name.split("\n")[0].strip()
        keyboard_buttons.append([InlineKeyboardButton(f"⚙️ Manage: {clean_name}", callback_data=f"manage_{ch['item_id']}")])
        
    if keyboard_buttons:
        await message.reply_text(
            "📑 <b>ʏᴏᴜʀ  ɪɴᴠᴇɴᴛᴏʀʏ:</b>\nNiche kisi bhi item ko manage karein:", 
            reply_markup=InlineKeyboardMarkup(keyboard_buttons), 
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text("❌ Abhi koi item add nahi hai.")


@Client.on_callback_query(filters.regex("^manage_"))
async def manage_ch(client, call):
    if call.from_user.id != config.ADMIN_ID:
        return await call.answer("Unauthorized!", show_alert=True)
        
    item_id = call.data.split('_')[1]
    ch_data = await db.find_single_story({"item_id": item_id})
    if not ch_data: 
        return await call.answer("Data not found!", show_alert=True)

    bot_info = await client.get_me()
    link = f"https://t.me/{bot_info.username}?start={item_id}"
    
    raw_name = ch_data.get('name') or "Unnamed Item"
    clean_name = raw_name.split("\n")[0].strip()
    
    source_platform = ch_data.get('source', 'none') 
    validity_info = ch_data.get('validity', 'N/A')
    price_info = ch_data.get('price', '0')
    
    text = (
        f"⚙️ <b>sᴇᴛᴛɪɴɢs:</b> {clean_name}\n"
        f"────────────────────\n"
        f"📂 <b>source:</b> <code>{source_platform}</code>\n"
        f"⏱️ <b>validity:</b> {validity_info} Din\n"
        f"💰 <b>price:</b> ₹{price_info}\n"
        f"📺 <b>demo:</b> {ch_data.get('demo_link', 'None')}\n\n"
        f"🔗 <b>sʜᴀʀᴇ ʟɪɴᴋ:</b>\n<code>{link}</code>\n"
        f"────────────────────"
    )
    try: 
        await call.message.delete()
    except: 
        pass

    photo_id = ch_data.get('file_id')
    if photo_id:
        await client.send_photo(call.message.chat.id, photo=photo_id, caption=text, parse_mode=enums.ParseMode.HTML)
    else:
        await client.send_message(call.message.chat.id, text=text, parse_mode=enums.ParseMode.HTML)


# =====================================================================
# ─── 3. FORWARD CHANNEL STORY FLOW (/add) ───
# =====================================================================
@Client.on_message(filters.command("add") & filters.private & filters.incoming)
async def add_start(client, message):
    if message.from_user.id != config.ADMIN_ID: 
        return
    
    ADMIN_MGMT_STATES[message.from_user.id] = {"step": "awaiting_forward"}
    await message.reply_text(
        "📢 <b>ᴀ_ᴅ_ᴅ  ᴄ_ʜ_ᴀ_ɴ__ɴ_ᴇ_ʟ:</b>\n\n"
        "➔ Jis channel ko add karna hai, us channel ka koi bhi ek post yahan <b>Forward</b> karein:", 
        parse_mode=enums.ParseMode.HTML
    )


# =====================================================================
# ─── 4. STANDALONE MANUAL COMBO FIXED ───
# =====================================================================
@Client.on_message(filters.command("add_combo") & filters.private & filters.incoming)
async def add_combo_start(client, message):
    if message.from_user.id != config.ADMIN_ID: 
        return
    
    ADMIN_MGMT_STATES[message.from_user.id] = {"step": "combo_name"}
    await message.reply_text(
        "🎁 <b>ᴍ_ᴀ_ɴ_ᴜ_ᴀ_ʟ  ᴄ_ᴏ_ᴍ_ʙ_ᴏ  s_ᴇ_ᴛ_ᴜ_ᴘ:</b>\n\n"
        "➔ Combo Pack ka Jo Naam <u>Store Board</u> par dikhana hai, wo bhejiyen:", 
        parse_mode=enums.ParseMode.HTML
    )


# =====================================================================
# ─── CENTRAL ASYNC INTEGRATED ROUTER SWITCHBOARD (STEPS LAYER) ───
# =====================================================================
@Client.on_message(filters.private & filters.incoming, group=4)
async def admin_central_router_engine(client, message):
    user_id = message.from_user.id
    state = ADMIN_MGMT_STATES.get(user_id)
    
    if not state:
        return 

    # CRITICAL FIX: Direct text routing bypass standard commands to prevent instant loops
    if message.text and message.text.strip().startswith("/"):
        if message.text.strip() == "/cancel":
            ADMIN_MGMT_STATES.pop(user_id, None)
            return await message.reply_text("❌ Action cancelled.")
        return

    step = state.get("step")

    # ─────────────── REMOVE USER BLOCK ───────────────
    if step == "awaiting_remove_id":
        try:
            u_id = int(message.text.strip())
            ADMIN_MGMT_STATES.pop(user_id, None)
            
            result = await db.db.users_col.delete_many({"user_id": u_id})
            if result.deleted_count > 0:
                await message.reply_text(f"✅ <b>Success!</b>\nUser <code>{u_id}</code> ka access hata diya gaya.", parse_mode=enums.ParseMode.HTML)
                try: 
                    await client.send_message(chat_id=u_id, text="⚠️ <b>Access Revoked:</b> Aapka subscription khatam kar diya gaya hai.")
                except: 
                    pass
            else:
                await message.reply_text("❓ Is ID ka koi active subscription nahi mila.")
        except ValueError:
            await message.reply_text("❌ Invalid ID! Sirf numbers bhejein.")

    # ─────────────── /add FORWARDED FLOW BLOCKS ───────────────
    elif step == "awaiting_forward":
        is_forwarded = (
            message.forward_from_chat or 
            message.forward_from or 
            message.forward_date
        )

        if is_forwarded:
            if message.forward_from_chat:
                ch_id = message.forward_from_chat.id
                ch_name = message.forward_from_chat.title.split("\n")[0].strip()
            else:
                ch_id = message.chat.id
                ch_name = "Private/Hidden Channel"
            
            state["ch_id"] = ch_id
            state["ch_name"] = ch_name
            state["step"] = "add_validity"
            ADMIN_MGMT_STATES[user_id] = state
            
            await message.reply_text(
                f"✅ <b>Channel Detected:</b> {ch_name}\n🆔 <b>ID:</b> <code>{ch_id}</code>\n\n"
                f"⏱️ <b>⏳ ᴠᴀʟɪᴅɪᴛʏ:</b>\nYeh data kitne din tak valid rakhna hai? (Sirf numbers likhein, jaise: 30):", 
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text("❌ Galat Input! Kripya channel se post forward karein (ya /cancel):")

    elif step == "add_validity":
        if not message.text or not message.text.isdigit():
            return await message.reply_text("❌ Validity sirf number me bhejiyen:")
            
        state["validity_days"] = message.text.strip()
        state["step"] = "add_price"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text(
            f"💰 <b>ᴘʀɪᴄɪɴɢ:</b>\nIs <code>{state['validity_days']}</code> Din ke liye kitna <b>Price (₹)</b> rakhna hai? (Jaise: 49):",
            parse_mode=enums.ParseMode.HTML
        )

    elif step == "add_price":
        if not message.text or not message.text.isdigit():
            return await message.reply_text("❌ Price sirf number me bhejiyen:")
            
        state["price"] = message.text.strip()
        state["step"] = "add_photo"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text(
            "🖼️ <b><b>ᴄʜᴀɴɴᴇʟ ᴘʜᴏᴛᴏ:</b></b>\nAap is channel ke liye koi custom photo lagana chahte hain?\n\n"
            "➔ Ek <b>Photo</b> bhejein.\n➔ Ya bina photo ke aage badhne ke liye <code>skip</code> likhein:",
            parse_mode=enums.ParseMode.HTML
        )

    elif step == "add_photo":
        file_id = message.photo.file_id if message.photo else None
        if not message.photo and message.text and message.text.lower() != "skip":
            return await message.reply_text("❌ Photo send karein ya <code>skip</code> likhein:")

        state["file_id"] = file_id
        state["step"] = "add_demo"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text("🔗 <b>Demo Link bhejein</b> (Ya 'skip' ya 'none' likhein):")

    elif step == "add_demo":
        raw_text = message.text.strip() if message.text else ""
        demo = None if raw_text.lower() in ['none', 'skip', ''] else raw_text
        ADMIN_MGMT_STATES.pop(user_id, None)

        state_id = str(uuid.uuid4())[:8]
        ADMIN_MGMT_STATES[f"temp_{state_id}"] = {
            "ch_id": state["ch_id"], 
            "ch_name": state["ch_name"],
            "validity_days": state["validity_days"], 
            "price": state["price"],
            "file_id": state["file_id"],
            "demo_link": demo
        }
        
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("pocket", callback_data=f"newsrc_pocket_{state_id}"),
                InlineKeyboardButton("pratilipi", callback_data=f"newsrc_pratilipi_{state_id}")
            ]
        ])
        await message.reply_text("📂 <b>Select Category:</b>", reply_markup=markup, parse_mode=enums.ParseMode.HTML)

    # ─────────────── /add_combo MANUAL PACK FLOW BLOCKS ───────────────
    elif step == "combo_name":
        if not message.text:
            return await message.reply_text("❌ Valid Combo text name bhejein:")
            
        state["combo_name"] = message.text.split("\n")[0].strip()
        state["step"] = "combo_validity"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text(
            "⏱️ <b>⏳ ᴠᴀʟɪᴅɪᴛʏ:</b>\nYeh combo bundle kitne din tak valid rahega? (Jaise: 30):",
            parse_mode=enums.ParseMode.HTML
        )

    elif step == "combo_validity":
        if not message.text or not message.text.isdigit():
            return await message.reply_text("❌ Validity sirf numbers me bhejiyen:")
            
        state["validity_days"] = message.text.strip()
        state["step"] = "combo_price"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text(
            "💰 <b><b>ᴘʀɪᴄɪɴɢ:</b></b>\nIs total combo package ka <b>Price (₹)</b> kitna rakhna hai? (Jaise: 149):",
            parse_mode=enums.ParseMode.HTML
        )

    elif step == "combo_price":
        if not message.text or not message.text.isdigit():
            return await message.reply_text("❌ Price sirf numbers me bhejiyen:")
            
        state["price"] = message.text.strip()
        state["step"] = "combo_photo"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text(
            "🖼️ <b><b>ᴄᴏᴍʙᴏ ᴘʜᴏᴛᴏ:</b></b>\nIs bundle banner ke liye koi photo lagani hai?\n\n"
            "➔ Ek <b>Photo</b> send karein.\n➔ Ya skip karne ke liye <code>skip</code> likhein:",
            parse_mode=enums.ParseMode.HTML
        )

    elif step == "combo_photo":
        file_id = message.photo.file_id if message.photo else None
        if not message.photo and message.text and message.text.lower() != "skip":
            return await message.reply_text("❌ Photo send karein ya <code>skip</code> likhein:")
            
        state["file_id"] = file_id
        state["step"] = "combo_demo"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text("🔗 <b>Demo Link bhejein</b> (Ya 'skip' ya 'none' likhein):")

    elif step == "combo_demo":
        raw_text = message.text.strip() if message.text else ""
        state["demo_link"] = None if raw_text.lower() in ['none', 'skip', ''] else raw_text
        state["step"] = "combo_channels"
        ADMIN_MGMT_STATES[user_id] = state
        
        await message.reply_text(
            "🆔 <b><b>ᴄʜᴀɴɴᴇʟ ɪᴅs ʟɪsᴛ:</b></b>\nIs combo bundle ke andar aane wale saare channels ki <b>IDs</b> comma ( , ) laga kar dein:\n\n"
            "➔ <code>-100123456,-100987654</code>",
            parse_mode=enums.ParseMode.HTML
        )

    elif step == "combo_channels":
        if not message.text:
            return await message.reply_text("❌ Channel IDs bhejiyen:")
            
        raw_ids = message.text.strip().replace(" ", "")
        try:
            channel_ids_list = [int(cid) for cid in raw_ids.split(",") if cid]
        except ValueError:
            return await message.reply_text("❌ <b>Format Error!</b> Keval IDs aur comma ka use karein. Dobara valid IDs bhejein:")

        ADMIN_MGMT_STATES.pop(user_id, None)
        item_id = f"combo_{str(uuid.uuid4())[:10]}"
        
        await db.db.channels_col.insert_one({
            "item_id": item_id,
            "name": state["combo_name"],
            "combo_name": state["combo_name"],       
            "is_combo": True,               
            "validity": state["validity_days"],
            "price": state["price"],                 
            "file_id": state["file_id"],
            "demo_link": state["demo_link"],
            "channels_list": channel_ids_list,
            "source": "combo",              
            "type": "combo"
        })
        
        bot_info = await client.get_me()
        bot_link = f"https://t.me/{bot_info.username}?start={item_id}"
        
        # CRITICAL FIXED: Cleaned f-string literal values to avoid backslash interpolation errors
        c_name = state['combo_name']
        v_days = state['validity_days']
        c_price = state['price']
        ch_count = len(channel_ids_list)
        
        success_text = (
            f"🎁 <b>sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ sᴀᴠᴇᴅ ɪɴ sᴛᴏʀᴇ!</b>\n"
            f"──────────────────────────\n"
            f"🎁 <b>ᴄᴏᴍʙᴏ ɴᴀᴍᴇ:</b> <code>{c_name}</code>\n"
            f"⏱️ <b>ᴠᴀʟɪᴅɪᴛʏ:</b> {v_days} Din\n"
            f"💰 <b>ᴘʀɪᴄᴇ:</b> ₹{c_price}\n"
            f"📊 <b>ᴄʜᴀɴɴᴇʟs:</b> {ch_count} Linked\n\n"
            f"🔗 <b>sʜᴀʀᴇ ʟɪɴᴋ (ᴜsᴇʀs):</b>\n<code>{bot_link}</code>\n"
            f"──────────────────────────"
        )
        
        if state["file_id"]:
            await client.send_photo(chat_id=message.chat.id, photo=state["file_id"], caption=success_text, parse_mode=enums.ParseMode.HTML)
        else:
            await message.reply_text(success_text, parse_mode=enums.ParseMode.HTML)


# =====================================================================
# ─── 5. CALLBACK & FINAL SAVE (STRICT FOR FORWARDED STORIES) ───
# =====================================================================
@Client.on_callback_query(filters.regex("^newsrc_"))
async def handle_category_selection(client, call):
    if call.from_user.id != config.ADMIN_ID: 
        return await call.answer("Unauthorized!", show_alert=True)
    
    parts = call.data.split('_')
    platform = "pocket" if parts[1] == "pocket" else "pratilipi"
    state_id = parts[2]
    
    data = ADMIN_MGMT_STATES.get(f"temp_{state_id}")
    if not data:
        return await call.answer("Session Expired! Dubara /add karein.", show_alert=True)
    
    try: 
        await call.message.delete()
    except: 
        pass
    
    item_id = str(uuid.uuid4())[:10]
    ADMIN_MGMT_STATES.pop(f"temp_{state_id}", None)
    
    await db.db.channels_col.update_one(
        {"item_id": item_id}, 
        {"$set": {
            "item_id": item_id,
            "channel_id": data["ch_id"],
            "name": data["ch_name"], 
            "story_name": data["ch_name"], 
            "validity": data["validity_days"], 
            "price": data["price"],        
            "file_id": data["file_id"],
            "demo_link": data["demo_link"],
            "source": platform,            
            "type": "channel"
        },
        "$unset": {
            "is_combo": ""                 
        }}, 
        upsert=True
    )
    
    bot_info = await client.get_me()
    bot_link = f"https://t.me/{bot_info.username}?start={item_id}"
    
    v_days = data['validity_days']
    u_price = data['price']
    d_link = data['demo_link'] if data['demo_link'] else 'None'
    
    success_text = (
        f"✅ <b>sᴛᴏʀỹ  sᴇᴛᴜᴘ  ... ɪɴɪsʜᴇᴅ!</b>\n"
        f"──────────────────────────\n"
        f"📂 <b>source:</b> <code>{platform}</code>\n"
        f"⏱️ <b>validity:</b> {v_days} Din\n"
        f"💰 <b>price:</b> ₹{u_price}\n"
        f"📺 <b>demo:</b> {d_link}\n\n"
        f"🔗 <b>sʜᴀʀᴇ ʟɪɴᴋ (ꜰᴏʀ ᴜsᴇʀs):</b>\n<code>{bot_link}</code>\n"
        f"──────────────────────────"
    )
    
    if data["file_id"]:
        await client.send_photo(chat_id=call.message.chat.id, photo=data["file_id"], caption=success_text, parse_mode=enums.ParseMode.HTML)
    else:
        await client.send_message(chat_id=call.message.chat.id, text=success_text, parse_mode=enums.ParseMode.HTML)
