# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import time
import urllib.parse
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove
)
from plugins.dbusers import db  # Aapki database wrapper instance
import config

# Global processing tracking to monitor screenshot submissions
USER_PAYMENT_STATES = {}

# ===================================================
# --- EXTRA CONFIG: FRESH START MENU RE-LOAD ---
# ===================================================
async def send_home_menu(client, chat_id):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_to_start")]
    ])
    await client.send_message(
        chat_id=chat_id,
        text="❌ <b>ᴘᴀʏᴍᴇɴᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ!</b>\n\nAapka current payment process rok diya gaya hai. Aap niche diye gaye menu se fir se shuru kar sakte hain:",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )


# --- 1. PAYMENT SELECTION ROUTER (CONNECTED WITH NEW STORE LAYER) ---
@Client.on_callback_query(filters.regex("^pay_"))
async def confirm_step(client, call):
    db_id = call.data.split('_')[1]
    
    # Database object fetch lookup pipeline from motor async integration
    data = await db.find_single_story({"item_id": db_id}) or \
           await db.find_single_story({"channel_id": int(db_id) if db_id.replace('-','').isdigit() else 0}) or \
           await db.find_single_story({"_id": db_id})
    
    if not data: 
        return await call.answer(f"❌ Data not found! (ID: {db_id})", show_alert=True)

    # Dynamic pricing validation rules setup
    if data.get('is_combo'):
        price = data['price']
        display_name = data.get('combo_name', 'Premium Combo')
        mins = "manual"
    elif 'story_name' in data:
        price = data['price']
        display_name = data.get('story_name').split("\n")[0].strip() # First line tracking rule
        mins = "manual"
    else:
        mins = "manual"  # Default fallback state identifier
        price = data.get('price', '49')
        display_name = data.get('name', 'Premium Channel')
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 ᴘᴀʏ ᴠɪ VIA ǫʀ sᴄᴀɴ", callback_data=f"man_{db_id}_{mins}_qr")],
        [InlineKeyboardButton("📲 ᴘᴀʏ ᴠɪ VIA ᴜᴘɪ ɪᴅ", callback_data=f"man_{db_id}_{mins}_upi")],
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])
    
    text = (
        f"<b>🛒 ᴄᴏɴғɪʀᴍ sᴇʟᴇᴄᴛɪᴏɴ</b>\n"
        f"────────────────────\n"
        f"📦 ɪᴛᴇᴍ: <b>{display_name}</b>\n"
        f"💰 ᴀᴍᴏᴜɴᴛ: <b>₹{price}</b>\n\n"
        f"➔ Payment method select karein:"
    )
    
    try:
        await call.message.delete()
    except:
        pass

    await client.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


# --- 2. MANUAL PAYMENT EXECUTION GATEWAY ---
@Client.on_callback_query(filters.regex("^man_"))
async def manual_pay(client, call):
    parts = call.data.split('_')
    mode = parts[-1]                
    mins = parts[-2]                
    db_id = "_".join(parts[1:-2]) 
    
    data = await db.find_single_story({"item_id": db_id}) or \
           await db.find_single_story({"channel_id": int(db_id) if db_id.replace('-','').isdigit() else 0}) or \
           await db.find_single_story({"_id": db_id})
    
    if not data:
        return await call.answer("❌ Data Error on Payment!", show_alert=True)

    price = data['price'] if (data.get('is_combo') or 'story_name' in data) else data.get('price', '49')
        
    upi_string = f"upi://pay?pa={config.UPI_ID}&am={price}&cu=INR&tn=Pay_{db_id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_string)}"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ sᴜʙᴍɪᴛ sᴄʀᴇᴇɴsʜᴏᴛ", callback_data=f"paid_{db_id}_{mins}")],
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])

    try:
        await call.message.delete()
    except:
        pass

    if mode == "qr":
        await client.send_photo(call.message.chat.id, qr_url, caption=f"📥 <b>ǫʀ sᴄᴀɴɴᴇʀ</b>\n\nAmount: <b>₹{price}</b>\n\n➔ Pay karke niche wala button dabayein.", reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    else:
        await client.send_message(call.message.chat.id, f"📲 <b>ᴜᴘɪ ɪᴅ:</b> <code>{config.UPI_ID}</code>\nAmount: <b>₹{price}</b>\n\n➔ Pay karne ke baad niche button dabayein.", reply_markup=markup, parse_mode=enums.ParseMode.HTML)


# --- 3. DIRECT SCREENSHOT LISTENER SWITCH ---
@Client.on_callback_query(filters.regex("^paid_"))
async def handle_paid(client, call):
    parts = call.data.split('_')
    mins = parts[-1]
    db_id = "_".join(parts[1:-1])
    await call.answer()
    
    try:
        await call.message.delete()
    except:
        pass
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])
        
    await client.send_message(
        chat_id=call.message.chat.id, 
        text="📸 Payment ka <b>Screenshot</b> bhejein:\n\n➔ <i>Agar cancel karna chahte hain toh niche button par click karein ya chat me <code>/cancel</code> likhein.</i>", 
        reply_markup=markup, 
        parse_mode=enums.ParseMode.HTML
    )
    # User step listener locked inside session state map
    USER_PAYMENT_STATES[call.from_user.id] = {"item_id": db_id, "mins": mins, "awaiting_screenshot": True}


# Central tracking pipeline listening exclusively for screenshot upload actions
@Client.on_message(filters.private & filters.incoming, group=2)
async def payment_screenshot_handler(client, message):
    user_id = message.from_user.id
    state = USER_PAYMENT_STATES.get(user_id)
    
    if not state or not state.get("awaiting_screenshot"):
        return # Skip processing if user is not executing an active transaction
        
    if message.text and message.text.lower() in ['/cancel', 'cancel']:
        USER_PAYMENT_STATES.pop(user_id, None)
        return await send_home_menu(client, message.chat.id)

    if not message.photo:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
        ])
        return await message.reply_text(
            "❌ Please sirf Photo (Screenshot) bhejein!\nCancel karne ke liye <code>/cancel</code> likhein ya neeche click karein:", 
            reply_markup=markup, 
            parse_mode=enums.ParseMode.HTML
        )
    
    item_id = state["item_id"]
    mins = state["mins"]
    USER_PAYMENT_STATES.pop(user_id, None) # Core verification state release
    
    photo_id = message.photo.file_id
    data = await db.find_single_story({"item_id": item_id}) or \
           await db.find_single_story({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0}) or \
           await db.find_single_story({"_id": item_id})
    
    if not data:
        return await message.reply_text("❌ Something went wrong, item not found!")

    display_name = data.get('combo_name') or data.get('story_name') or data.get('name')
    if display_name and "\n" in display_name:
        display_name = display_name.split("\n")[0].strip()

    await message.reply_text("⏳ <b>ʀᴇǫᴜᴇsᴛ sᴇɴᴛ!</b>\nAdmin check karke aapka access on kar dega.", parse_mode=enums.ParseMode.HTML)
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}_{item_id}_{mins}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}"), 
         InlineKeyboardButton("💬 Support", url=f"tg://openmessage?user_id={user_id}")]
    ])
    
    admin_text = f"📥 <b>ɴᴇᴡ ᴘᴀʏᴍᴇɴᴛ ʀᴇǫᴜᴇsᴛ</b>\n────────────────────\n👤 User ID: <code>{user_id}</code>\n📦 Item: <b>{display_name}</b>\n⏳ Plan: {mins if mins != 'manual' else 'Lifetime'}"
    await client.send_photo(chat_id=config.ADMIN_ID, photo=photo_id, caption=admin_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex("^cancel_payment$"))
async def process_inline_cancel(client, call):
    await call.answer("Process Cancelled!")
    USER_PAYMENT_STATES.pop(call.from_user.id, None)
    try:
        await call.message.delete()
    except:
        pass
    await send_home_menu(client, call.message.chat.id)


# --- 4. ADMIN APPROVAL DISPATCH SYSTEM ---
@Client.on_callback_query(filters.regex("^app_"))
async def admin_approve(client, call):
    parts = call.data.split('_')
    u_id = parts[1]
    mins = parts[-1]
    item_id = "_join".join(parts[2:-1]) if "_join" in call.data else "_".join(parts[2:-1])
    
    data = await db.find_single_story({"item_id": item_id}) or \
           await db.find_single_story({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0}) or \
           await db.find_single_story({"_id": item_id})
    
    if not data: 
        return await call.answer("❌ Data not found on Approval!", show_alert=True)
    
    expiry = int(time.time()) + (int(mins) * 60) if mins != 'manual' else int(time.time()) + (365*24*60*60)
    inline_buttons = []

    # ─── CASE A: COMBO PACK DISTRIBUTION PIPELINE ───
    if data.get('is_combo') and 'channels_list' in data:
        msg = "🎁 <b>ᴄᴏᴍʙᴏ ᴘᴀᴄᴋ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\nAapko sabhi linked channels ka access de diya gaya hai. Niche diye buttons se join karein:\n\n"
        for ch_id in data['channels_list']:
            # Database storage operations matching dynamic update rules
            await db.db.users_col.update_one({"user_id": int(u_id), "channel_id": int(ch_id)}, {"$set": {"expiry": expiry}}, upsert=True)
            try:
                invite = await client.create_chat_invite_link(int(ch_id), member_limit=1)
                ch_info = await db.find_single_story({"channel_id": int(ch_id)})
                ch_title = ch_info.get('name') or ch_info.get('story_name') if ch_info else f"VIP Channel {ch_id}"
                if ch_title and "\n" in ch_title:
                    ch_title = ch_title.split("\n")[0].strip()
                inline_buttons.append([InlineKeyboardButton(f"📢 Join: {ch_title}", url=invite.invite_link)])
            except Exception as e:
                print(f"Combo Link Error: {e}")
        msg += "⚠️ <i>Links single-use hain, ek baar join hone ke baad automatic expire ho jayengi!</i>"

    # ─── CASE B: ROUTED GENERAL TELEGRAM CHANNEL ───
    elif data.get('type') == 'channel' or ('channel_id' in data and data.get('source') not in ['pocket', 'pratilipi'] and not data.get('is_combo')):
        target_channel = int(data['channel_id'])
        await db.db.users_col.update_one({"user_id": int(u_id), "channel_id": target_channel}, {"$set": {"expiry": expiry}}, upsert=True)
        try:
            invite = await client.create_chat_invite_link(chat_id=target_channel, member_limit=1)
            inline_buttons.append([InlineKeyboardButton("🔐 JOIN PREMIUM CHANNEL", url=invite.invite_link)])
            
            validity_display = data.get('validity', mins)
            msg = (
                f"✅ <b>ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\n"
                f"📂 <b>ᴄʜᴀɴɴᴇʟ:</b> <b>{data.get('name', 'VIP Channel')}</b>\n"
                f"⏱️ <b>ᴠᴀʟɪᴅɪᴛʏ:</b> {validity_display if validity_display != 'manual' else 'Lifetime'}\n\n"
                f"Join karne ke liye neeche button par click karein:\n\n"
                f"⚠️ <i>Yeh link single use hai, ek baar use hone ke baad automatic expire ho jayegi!</i>"
            )
        except Exception as e: 
            print(f"Error: {e}")
            msg = "✅ <b>ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\nBot link generate nahi kar saka, admin rights setup check karein."

    # ─── CASE C: PREMIUM STORY INTERNAL FLOW ───
    else:
        await db.db.users_col.update_one({"user_id": int(u_id), "channel_id": data.get('channel_id', 0)}, {"$set": {"expiry": expiry}}, upsert=True)
        target_link = data.get('bot_link') or data.get('final_link') or 'https://t.me'
        
        inline_buttons.append([InlineKeyboardButton("🚀 sᴛᴀʀᴛ sᴛᴏʀỹ", url=target_link)])
        
        platform_info = f"\n📂 Platform: <code>{data.get('source')}</code>" if data.get('source') else ""
        msg = (
            f"🎉 <b>ᴘᴀʏᴍᴇɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n"
            f"────────────────────\n"
            f"📖 <b>sᴛᴏʀỹ:</b> {data.get('story_name', 'Premium Story').split('\n')[0].strip()}"
            f"{platform_info}\n"
            f"💰 <b>ᴘʀɪᴄᴇ:</b> ₹{data.get('price', '49')}\n"
            f"────────────────────\n"
            f"➔ Niche diye gaye button par click karke apni full story access karein 👇"
        )

    try:
        markup = InlineKeyboardMarkup(inline_buttons)
        if 'story_name' in data and data.get('file_id') and data.get('type') != 'channel':
            await client.send_photo(chat_id=int(u_id), photo=data['file_id'], caption=msg, reply_markup=markup, protect_content=True)
        else:
            await client.send_message(chat_id=int(u_id), text=msg, reply_markup=markup, protect_content=True)
    except Exception as e:
        print(f"Delivery Error: {e}")
        
    await client.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        caption=f"✅ Approved for User: {u_id}"
    )


@Client.on_callback_query(filters.regex("^rej_"))
async def admin_reject(client, call):
    u_id = call.data.split('_')[1]
    await client.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        caption="❌ Payment Rejected!"
    )
    await client.send_message(chat_id=int(u_id), text="❌ Aapka payment reject ho gaya hai. Support se baat karein.")
