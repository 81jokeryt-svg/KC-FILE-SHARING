# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pyrogram import Client, filters, enums
from pyrogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove
)
from plugins.dbusers import db

# User states pagination track karne ke liye
USER_STORE_STATES = {}

# ─── 1. BOTTOM KEYBOARD CATEGORIES MENU ───
def get_platform_markup():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Pratilipi FM"), KeyboardButton("Pocket FM")],
            [KeyboardButton("Other")],
            [KeyboardButton("« Back to Menu")]
        ],
        resize_keyboard=True
    )

def get_categories_markup():
    return get_platform_markup()


# ─── 2. PAGINATED ITEMS MENU ENGINE ───
async def get_store_pagination_markup(category_type, page=1):
    limit = 8
    skip = (page - 1) * limit
    
    if category_type == "pratilipi":
        query = {"story_name": {"$exists": True}, "source": "pratilipi", "is_combo": {"$exists": False}}
    elif category_type == "pocket":
        query = {"story_name": {"$exists": True}, "source": "pocket", "is_combo": {"$exists": False}}
    elif category_type == "combo":
        query = {"is_combo": True}
    else:
        query = {}
        
    total_items = await db.count_stories_by_filter(query)
    
    if total_items == 0:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("🚫 STORE IS EMPTY")],
                [KeyboardButton("🔙 BACK TO CATEGORIES")]
            ], 
            resize_keyboard=True
        )

    sliced_items = await db.get_stories_by_filter(query, skip, limit)
    keyboard_buttons = []

    for index, item in enumerate(sliced_items, start=skip + 1):
        if category_type == "combo":
            btn_text = f"🎁 {index}. {item.get('combo_name', 'Unnamed Combo')} ➔ [ ₹{item['price']} ]"
            keyboard_buttons.append([KeyboardButton(btn_text)])
        else:
            raw_title = item.get('story_name') or item.get('name') or 'Unnamed Story'
            clean_title = raw_title.split("\n")[0].strip()
            btn_text = f"{index}. {clean_title} [ ₹{item.get('price', '49')} ]"
            keyboard_buttons.append([KeyboardButton(btn_text)])
            
    nav_buttons = []
    if page > 1:
        nav_buttons.append(KeyboardButton("‹ PREV"))
    if (skip + limit) < total_items:
        nav_buttons.append(KeyboardButton("NEXT ›"))
        
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
        
    keyboard_buttons.append([KeyboardButton("🔙 BACK TO CATEGORIES"), KeyboardButton("❌ CLOSE STORE")])
    return ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True)


# ─── 3. INTERMEDIATE LAYOUT ENGINE (Dono flows ke liye same Details Card) ───
async def show_story_details_by_id(client, chat_id, data):
    """Deep link ya keyboard click dono par pehle Cover Photo aur Confirm button dikhane ke liye"""
    inline_markup = []
    db_id = str(data.get('item_id') or data.get('channel_id') or data.get('_id'))

    if data.get('is_combo'):
        header = "🎁 <b><u>✨ ᴘʀᴇᴍɪᴜᴍ sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ ʙᴜɴᴅʟᴇ ✨</u></b>"
        item_label = data.get('combo_name', 'Premium Combo Pack')
        desc_text = f"📝 <b>sᴛᴏʀỹ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:</b>\n<i>{data.get('description', 'All premium files included.')}</i>"
    else:
        src_name = str(data.get('source', 'audio')).upper()
        header = f"🔥 <b><u>✨ ᴘʀᴇᴍɪᴜᴍ ᴇxᴄʟᴜsɪᴠᴇ sᴛᴏʀỹ ({src_name}) ✨</u></b>"
        raw_lbl = data.get('story_name') or data.get('name') or 'Premium Story'
        item_label = raw_lbl.split("\n")[0].strip()
        desc_text = "🤖 <b>ᴅᴇʟɪᴠᴇʀỹ:</b> <code><b>ɪɴsᴛᴀɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴀᴄᴄᴇss</b></code>"

    # ✅ Dono flows me pehle yehi single button dikhega jo payment file me lekar jayega
    inline_markup.append([InlineKeyboardButton("✅ CONFIRM", callback_data=f"pay_{db_id}")])
    
    if data.get('demo_link'):
        inline_markup.append([InlineKeyboardButton("📺 ᴠɪᴇᴡ ǫᴜᴀʟɪᴛỹ ᴅᴇᴍᴏ", url=data['demo_link'])])
        
    inline_markup.append([InlineKeyboardButton("⬅️ BACK TO LIST", callback_data="back_to_store_list")])

    details_layout = (
        f"{header}\n"
        "──────────────────────────\n"
        f"📦 <b><u>ɪᴛᴇᴍ ɴᴀᴍᴇ:</u></b> <code>{item_label}</code>\n"
        f"💰 <b><u>ᴘʀɪᴄᴇ:</u></b> <b>₹{data.get('price', '12')}</b>\n\n"
        f"{desc_text}\n"
        "──────────────────────────"
    )
    photo_id = data.get('file_id')

    if photo_id:
        await client.send_photo(chat_id, photo=photo_id, caption=details_layout, reply_markup=InlineKeyboardMarkup(inline_markup))
    else:
        await client.send_message(chat_id, text=details_layout, reply_markup=InlineKeyboardMarkup(inline_markup))


# ─── 4. TEXT MESSAGE CENTRAL ASYNC ROUTER ───
@Client.on_message(filters.text & filters.private & filters.incoming, group=1)
async def store_board_central_router(client, message):
    user_id = message.from_user.id
    text = message.text

    allowed_keywords = ["Pratilipi FM", "Pocket FM", "Other", "🔙 BACK TO CATEGORIES", "« Back to Menu", "❌ CLOSE STORE", "🚫 STORE IS EMPTY"]
    is_navigation = text in ["NEXT ›", "‹ PREV"]
    is_item_selection = any(char in text for char in ['[ ₹', '➔ [', '[₹'])

    if text not in allowed_keywords and not is_navigation and not is_item_selection:
        return 

    if text in ["« Back to Menu", "❌ CLOSE STORE"]:
        USER_STORE_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text("<b>Returning to Main Menu Dashboard...</b>", reply_markup=ReplyKeyboardRemove())

    if text == "🔙 BACK TO CATEGORIES":
        USER_STORE_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text("🎧 <b>Platform Selection</b>\n\nChoose a platform from the keyboard below:", reply_markup=get_platform_markup())

    category_map = {
        "Pratilipi FM": ("pratilipi", "✨ <b>ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs</b>"),
        "Pocket FM": ("pocket", "🎧 <b>ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs</b>"),
        "Other": ("combo", "🎁 <b>✨ ᴘʀᴇᴍɪᴜᴍ ᴄᴏᴍʙᴏ ᴘᴀᴄᴋs ✨</b>")
    }

    if text in category_map:
        cat_key, cat_header = category_map[text]
        USER_STORE_STATES[user_id] = {"category": cat_key, "page": 1}
        caption_text = f"{cat_header}\n\nAll available stories and their prices are shown in the menu below. Please tap on any story name from the keyboard menu."
        markup_keyboard = await get_store_pagination_markup(cat_key, page=1)
        return await message.reply_text(caption_text, reply_markup=markup_keyboard)

    if is_navigation:
        state = USER_STORE_STATES.get(user_id, {"category": "home", "page": 1})
        if state["category"] == "home":
            return
        state["page"] += 1 if text == "NEXT ›" else -1
        USER_STORE_STATES[user_id] = state
        markup_keyboard = await get_store_pagination_markup(state["category"], page=state["page"])
        return await message.reply_text(f"<b>✨ Page {state['page']} Packages:</b>", reply_markup=markup_keyboard)

    if is_item_selection:
        clean_name = text
        try:
            if "." in text:
                clean_name = text.split(".", 1)[1].split("[")[0].strip()
            else:
                clean_name = text.split("[")[0].strip()
            if "🎁" in text:
                clean_name = text.replace("🎁", "").split("➔")[0].strip()
        except Exception:
            pass

        state = USER_STORE_STATES.get(user_id, {"category": "pocket"})
        
        if state["category"] == "combo":
            data = await db.find_single_story({"combo_name": {"$regex": f"^{re.escape(clean_name)}", "$options": "i"}})
        else:
            data = await db.find_single_story({
                "$or": [
                    {"story_name": {"$regex": f"^{re.escape(clean_name)}", "$options": "i"}},
                    {"name": {"$regex": f"^{re.escape(clean_name)}", "$options": "i"}}
                ],
                "source": state["category"]
            })

        if not data:
            if state["category"] == "combo":
                data = await db.find_single_story({"combo_name": {"$regex": re.escape(clean_name), "$options": "i"}})
            else:
                data = await db.find_single_story({
                    "$or": [
                        {"story_name": {"$regex": re.escape(clean_name), "$options": "i"}},
                        {"name": {"$regex": re.escape(clean_name), "$options": "i"}
