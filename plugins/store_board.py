# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pyrogram import Client, filters
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

# ─── 1. BOTTOM KEYBOARD CATEGORIES MENU (KUKU REMOVED) ───
def get_categories_markup():
    """User ko niche reply keyboard me platforms dikhane ke liye"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Pratilipi FM"), KeyboardButton("Pocket FM")],
            [KeyboardButton("Other")],
            [KeyboardButton("« Back to Menu")]
        ],
        resize_keyboard=True
    )


# ─── 2. PAGINATED ITEMS MENU ENGINE (PRATILIPI + POCKET + COMBO) ───
async def get_store_pagination_markup(category_type, page=1):
    """Asynchronously matches database fields and slices items (8 items per page)"""
    limit = 8
    skip = (page - 1) * limit
    
    # Kuku filter dropped -> Pratilipi filter assigned dynamically
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

    # Display Loop with First Line Title Rule integration
    for index, item in enumerate(sliced_items, start=skip + 1):
        if category_type == "combo":
            btn_text = f"🎁 {index}. {item['combo_name']} ➔ [ ₹{item['price']} ]"
            keyboard_buttons.append([KeyboardButton(btn_text)])
        else:
            raw_title = item.get('story_name', 'Unnamed Story')
            # Title Split Logic: Sirf pehli line ko title banata hai
            clean_title = raw_title.split("\n")[0].strip()
            btn_text = f"{index}. {clean_title} [ ₹{item.get('price', '49')} ]"
            keyboard_buttons.append([KeyboardButton(btn_text)])
            
    # Navigation Buttons Setup
    nav_buttons = []
    if page > 1:
        nav_buttons.append(KeyboardButton("‹ PREV"))
    if (skip + limit) < total_items:
        nav_buttons.append(KeyboardButton("NEXT ›"))
        
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
        
    # Essential Standard Controls
    keyboard_buttons.append([KeyboardButton("🔙 BACK TO CATEGORIES"), KeyboardButton("❌ CLOSE STORE")])
    return ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True)


# ─── 3. TEXT MESSAGE ASYNC CENTRAL ROUTER ───
@Client.on_message(filters.text & filters.private & filters.incoming, group=1)
async def store_board_central_router(client, message):
    user_id = message.from_user.id
    text = message.text

    # Keywords strictly matched to new buttons
    allowed_keywords = ["Pratilipi FM", "Pocket FM", "Other", "🔙 BACK TO CATEGORIES", "« Back to Menu", "❌ CLOSE STORE", "🚫 STORE IS EMPTY"]
    is_navigation = text in ["NEXT ›", "‹ PREV"]
    is_item_selection = any(char in text for char in ['[ ₹', '➔ ['])

    if text not in allowed_keywords and not is_navigation and not is_item_selection:
        return 

    if text in ["« Back to Menu", "❌ CLOSE STORE"]:
        USER_STORE_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text(
            "<b>Returning to Main Menu Dashboard...</b>", 
            reply_markup=ReplyKeyboardRemove()
        )

    if text == "🔙 BACK TO CATEGORIES":
        USER_STORE_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text(
            "🎧 <b>Platform Selection</b>\n\nChoose a platform from the keyboard below:", 
            reply_markup=get_categories_markup()
        )

    # State Categories router map (Kuku replaced with Pratilipi)
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

    # Multi-page Switches Execution
    if is_navigation:
        state = USER_STORE_STATES.get(user_id, {"category": "home", "page": 1})
        if state["category"] == "home":
            return
            
        state["page"] += 1 if text == "NEXT ›" else -1
        USER_STORE_STATES[user_id] = state
        
        markup_keyboard = await get_store_pagination_markup(state["category"], page=state["page"])
        return await message.reply_text(
            f"<b>✨ Page {state['page']} Packages:</b>", 
            reply_markup=markup_keyboard
        )

    # Item Selection Processing Block (Hides reply keyboard layout)
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
        
        # Async Single document lookup based on active configuration
        if state["category"] == "combo":
            data = await db.find_single_story({"combo_name": clean_name})
        else:
            data = await db.find_single_story({"story_name": {"$regex": f"^{re.escape(clean_name)}"}, "source": state["category"]})

        if not data:
            return 

        loading_alert = await message.reply_text(
            "⏳ <i>Loading Story Details...</i>", 
            reply_markup=ReplyKeyboardRemove(), 
            parse_mode="html"
        )

        inline_markup = []
        db_id = str(data.get('item_id') or data.get('channel_id') or data.get('_id'))

        if data.get('is_combo'):
            inline_markup.append([InlineKeyboardButton(f"✅ CONFIRM & PAY COMBO - ₹{data['price']}", callback_data=f"pay_{db_id}")])
            header = "🎁 <b>ᴘʀᴇᴍɪᴜᴍ sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ ʙᴜɴᴅʟᴇ</b>"
            item_label = data.get('combo_name')
            desc_text = f"📝 <b>ɪɴᴄʟᴜᴅᴇᴅ sᴛᴏʀɪᴇs:</b>\n<i>{data.get('description', '')}</i>"
        else:
            inline_markup.append([InlineKeyboardButton(f"💳 UNLOCK PREMIUM STORY - ₹{data.get('price', '49')}", callback_data=f"pay_{db_id}")])
            header = f"🔥 <b>ᴘʀᴇᴍɪᴜᴍ ᴇxᴄʟᴜsɪᴠᴇ sᴛᴏʀʏ ({data.get('source', 'audio')})</b>"
            item_label = data.get('story_name').split("\n")[0].strip() # First line split check
            desc_text = "🤖 <b>**ᴅᴇʟɪᴠᴇʀʏ:**</b> <code><b>ɪɴsᴛᴀɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴀᴄᴄᴇss</b></code>"

        if data.get('demo_link'):
            inline_markup.append([InlineKeyboardButton("📺 ᴠɪᴇᴡ ǫᴜᴀʟɪᴛʏ ᴅᴇᴍᴏ", url=data['demo_link'])])
            
        inline_markup.append([InlineKeyboardButton("⬅️ BACK TO LIST", callback_data="back_to_store_list")])

        details_layout = f"{header}\n──────────────────────────\n📦 <b><u>ɪᴛᴇᴍ:</u></b> <code>{item_label}</code>\n\n{desc_text}\n──────────────────────────"
        photo_id = data.get('file_id')

        if photo_id:
            await client.send_photo(message.chat.id, photo=photo_id, caption=details_layout, reply_markup=InlineKeyboardMarkup(inline_markup))
        else:
            await client.send_message(message.chat.id, text=details_layout, reply_markup=InlineKeyboardMarkup(inline_markup))

        try:
            await loading_alert.delete()
        except:
            pass


# ─── 4. BACK TO LIST INLINE CALLBACK CONTROLLER ───
@Client.on_callback_query(filters.regex("^back_to_store_list$"))
async def process_return_store_callback(client, call):
    user_id = call.from_user.id
    await call.answer()
    try:
        await call.message.delete()
    except:
        pass
        
    state = USER_STORE_STATES.get(user_id, {"category": "pocket", "page": 1})
    markup_keyboard = await get_store_pagination_markup(state["category"], page=state["page"])
    
    await client.send_message(
        chat_id=call.message.chat.id, 
        text="👇 <i>Apni pasand ka item select karke full access lein:</i>", 
        reply_markup=markup_keyboard
    )
