import asyncio
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from plugins.dbusers import *
from utils import *

logger = logging.getLogger(__name__)

# Dictionary to track what admin is doing (State Management)
ADMIN_STATES = {}

def is_valid_domain(domain):
    pattern = r"^(?!:\/\/)([a-zA-Z0-9-_]+\.)*[a-zA-Z0-9][a-zA-Z0-9-_]+\.[a-zA-Z]{2,11}$"
    return bool(re.match(pattern, domain.strip()))

def is_valid_api(api):
    api_clean = api.strip()
    if " " in api_clean or len(api_clean) < 8:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_\-]+$", api_clean))

# --- LAYOUT GENERATORS ---
async def get_main_panel_layout(settings):
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    text = (
        "⚡ **BOT ADMIN CONTROL PANEL** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome back, Admin! Use the buttons below to configure and manage your bot settings instantly.\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 VERIFICATION & SWITCH MENU", callback_data="adm_sub_verify")],
        [InlineKeyboardButton("⏱️ AUTO DELETE MENU", callback_data="adm_sub_delete")],
        [InlineKeyboardButton("🎨 START PAGE CUSTOMIZER", callback_data="adm_sub_start_page")],
        [InlineKeyboardButton("👑 PREMIUM USER MENU", callback_data="adm_sub_premium")],
        [InlineKeyboardButton(f"🛡️ PROTECT CONTENT: {p_status}", callback_data="adm_toggle_protect")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_data")]
    ])
    return text, keyboard

async def get_verify_menu_layout(settings):
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    prem_mode_status = "🟢 ON" if settings.get("premium_mode", False) else "🔴 OFF"
    v_expire_hours = settings.get("verify_expire_time", 86400) // 3600
    text = (
        "🔐 **VERIFICATION & FEATURE SWITCH**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *Note: Ek waqt par sirf Verification chalega ya toh Premium Mode.*\n\n"
        f"🔗 **Shortener Site:** `{settings.get('shortlink_url')}`\n"
        f"🔑 **Shortener API:** `{settings.get('shortlink_api')}`\n"
        f"⏱️ **Token Validity:** `{v_expire_hours} Hours`"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification Mode: {v_status}", callback_data="adm_toggle_verify")],
        [InlineKeyboardButton(f"Premium Mode (Lock File): {prem_mode_status}", callback_data="adm_toggle_premium_mode")],
        [InlineKeyboardButton("Set Token Validity 🔑", callback_data="adm_set_token_time")],
        [InlineKeyboardButton("Change Shortener Link & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
    ])
    return text, keyboard

async def get_delete_menu_layout(settings):
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60
    text = (
        "⏱️ **AUTO DELETE CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ **Current Timer:** `{del_time} Minutes`"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Auto Delete Mode: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton("Set Delete Timer ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
    ])
    return text, keyboard

async def get_start_page_menu_layout(settings):
    has_photo = "🟢 Set (Custom)" if settings.get("start_photo") else "🔴 Not Set (Text Only)"
    has_text = "🟢 Custom Text Enabled" if settings.get("custom_start_text") else "⚪ Default Text Enabled"
    s_status = "🟢 ON (Blurred Image)" if settings.get("start_spoiler", False) else "🔴 OFF (Clear Image)"
    text = (
        "🎨 **START PAGE CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ **Start Photo Status:** `{has_photo}`\n"
        f"📝 **Start Text Status:** `{has_text}`\n"
        f"⚠️ **Spoiler Status:** `{s_status}`\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Set Start Text", callback_data="adm_set_start_txt"), 
         InlineKeyboardButton("🗑️ Reset Start Text", callback_data="adm_reset_start_txt")],
        [InlineKeyboardButton("🖼️ Set Start Photo", callback_data="adm_set_start_img"), 
         InlineKeyboardButton("🗑️ Remove Start Photo", callback_data="adm_remove_start_img")],
        [InlineKeyboardButton(f"🎭 Spoiler Mode: {'🟢 ON' if settings.get('start_spoiler', False) else '🔴 OFF'}", callback_data="adm_toggle_spoiler")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
    ])
    return text, keyboard

async def get_premium_menu_layout(settings):
    try: users_list = await db.get_all_premium_users(); total_premium = len(users_list)
    except: total_premium = 0
    current_buy_link = settings.get("premium_buy_link", "https://t.me/HDFILM0900_BOT")
    text = (
        "👑 **PREMIUM USER CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Total Premium Users:** `{total_premium}`\n"
        f"🔗 **Current Buy Link:** `{current_buy_link}`\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Premium ID", callback_data="adm_add_prem"),
         InlineKeyboardButton("🗑️ Remove Premium ID", callback_data="adm_rem_prem")],
        [InlineKeyboardButton("📜 View Premium Users", callback_data="adm_list_prem")],
        [InlineKeyboardButton("🔗 Set Buy Premium Link", callback_data="adm_set_buy_link")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
    ])
    return text, keyboard

# --- COMMANDS ---
@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    ADMIN_STATES[message.from_user.id] = None
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("open_admin_from_start"))
async def open_admin_from_start(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return
    ADMIN_STATES[query.from_user.id] = None
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
    await query.message.edit_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^adm_"))
async def admin_callback(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    action = query.data.replace("adm_", "")
    settings = await db.get_settings()
    chat_id = query.message.chat.id
    admin_id = query.from_user.id
    
    if action == "back_main":
        ADMIN_STATES[admin_id] = None
        text, keyboard = await get_main_panel_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return
        
    elif action == "sub_verify":
        text, keyboard = await get_verify_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return
        
    elif action == "sub_delete":
        text, keyboard = await get_delete_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return
        
    elif action == "sub_start_page":
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    elif action == "sub_premium":
        text, keyboard = await get_premium_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    elif action == "toggle_verify":
        new_val = not settings.get("verify_mode", True)
        await db.update_setting("verify_mode", new_val)
        if new_val: await db.update_setting("premium_mode", False)
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    elif action == "toggle_premium_mode":
        new_val = not settings.get("premium_mode", False)
        await db.update_setting("premium_mode", new_val)
        if new_val: await db.update_setting("verify_mode", False)
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return
        
    elif action == "toggle_delete":
        new_val = not settings.get("auto_delete_mode", True)
        await db.update_setting("auto_delete_mode", new_val)
        settings = await db.get_settings()
        text, keyboard = await get_delete_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return
        
    elif action == "toggle_protect":
        new_val = not settings.get("protect_content", False)
        await db.update_setting("protect_content", new_val)
        settings = await db.get_settings()
        text, keyboard = await get_main_panel_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    elif action == "toggle_spoiler":
        new_val = not settings.get("start_spoiler", False)
        await db.update_setting("start_spoiler", new_val)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    # --- STATE TRIGGERS ---
    elif action == "add_prem":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "ADD_PREM_UID", "prompt": await client.send_message(chat_id, "👑 **[STEP 1/2] Naye Premium User ki UID (Telegram ID) bhejein:**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "rem_prem":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "REM_PREM_UID", "prompt": await client.send_message(chat_id, "🗑️ **Premium se hatane ke liye User ki UID bhejein:**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "set_buy_link":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "SET_BUY_LINK", "prompt": await client.send_message(chat_id, "🔗 **Users ke liye Premium kharidne ka Link bhejein:**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "set_start_txt":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "SET_START_TXT", "prompt": await client.send_message(chat_id, "✍️ **Naya /start message text likh kar bhejein:**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "set_start_img":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "SET_START_IMG", "prompt": await client.send_message(chat_id, "🖼️ **Nayi Start Photo bhejein (As a Photo):**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "set_time":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "SET_DEL_TIME", "prompt": await client.send_message(chat_id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "set_token_time":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "SET_TOKEN_TIME", "prompt": await client.send_message(chat_id, "🔑 **Token Validity ka time Hours me bhejein:**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "change_link":
        await query.message.delete()
        ADMIN_STATES[admin_id] = {"state": "SET_SHORT_DOMAIN", "prompt": await client.send_message(chat_id, "🔗 **Naya Shortener Domain name bhejein (e.g. site.com):**\n\n*(Cancel ke liye /cancel likhein)*")}
    elif action == "reset_start_txt":
        await db.update_setting("custom_start_text", None)
        await query.answer("Reset successful!")
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
    elif action == "remove_start_img":
        await db.update_setting("start_photo", None)
        await query.answer("Image removed!")
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
    elif action == "list_prem":
        try: users = await db.get_all_premium_users()
        except: users = []
        list_text = "📜 **CURRENT PREMIUM USERS LIST**\n\n" + "\n".join([f"{i}. <code>{u}</code>" for i, u in enumerate(users, 1)]) if users else "<b>ℹ️ List khali hai!</b>"
        await query.message.edit_text(text=list_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_sub_premium")]]))

# --- TEXT/MEDIA INPUT HANDLER (REPLACES FREEZING LISTEN) ---
@Client.on_message(filters.user(ADMINS) & (filters.text | filters.photo), group=-1)
async def admin_state_processor(client, message):
    admin_id = message.from_user.id
    if admin_id not in ADMIN_STATES or not ADMIN_STATES[admin_id]:
        return

    current = ADMIN_STATES[admin_id]
    state = current["state"]
    prompt = current["prompt"]
    chat_id = message.chat.id
    
    u_text = message.text.strip() if message.text else ""
    
    # Global Cancel handling
    if u_text == "/cancel":
        try: await prompt.delete()
        except: pass
        try: await message.delete()
        except: pass
        ADMIN_STATES[admin_id] = None
        settings = await db.get_settings()
        text, keyboard = await get_main_panel_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    settings = await db.get_settings()

    try:
        if state == "ADD_PREM_UID":
            if not u_text.isdigit():
                await message.reply("❌ Shudh number bhejye UID mein! Re-try:")
                return
            target_id = int(u_text)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = {
                "state": "ADD_PREM_DAYS",
                "target_id": target_id,
                "prompt": await client.send_message(chat_id, f"⏱️ **[STEP 2/2] ID `{target_id}` ke liye DINO (Days) ki sankhya likhein:**")
            }
            return

        elif state == "ADD_PREM_DAYS":
            if not u_text.isdigit() or int(u_text) <= 0:
                await message.reply("❌ Valid Number bhejye! Re-try:")
                return
            target_id = current["target_id"]
            days = int(u_text)
            expiry = await db.add_premium_user(target_id, days)
            try: await prompt.delete(); await message.delete()
            except: pass
            
            await client.send_message(chat_id, f"✅ **Premium Activated!**\nID: `{target_id}`\nDays: `{days}`")
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "REM_PREM_UID":
            if not u_text.isdigit():
                await message.reply("❌ ID sirf number hoti hai! Re-try:")
                return
            try: await prompt.delete(); await message.delete()
            except: pass
            target_id = int(u_text)
            removed = await db.remove_premium_user(target_id)
            await client.send_message(chat_id, f"🗑️ ID `{target_id}` remove ho gayi!" if removed else "❌ ID mili nahi list me.")
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "SET_BUY_LINK":
            await db.update_setting("premium_buy_link", u_text)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "SET_START_TXT":
            await db.update_setting("custom_start_text", u_text)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_start_page_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "SET_START_IMG":
            if not message.photo:
                await message.reply("❌ Image format me send karein! Re-try:")
                return
            f_id = message.photo.file_id
            await db.update_setting("start_photo", f_id)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_start_page_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "SET_DEL_TIME":
            if not u_text.isdigit(): return
            await db.update_setting("auto_delete_time", int(u_text) * 60)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_delete_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "SET_TOKEN_TIME":
            if not u_text.isdigit(): return
            await db.update_setting("verify_expire_time", int(u_text) * 3600)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

        elif state == "SET_SHORT_DOMAIN":
            if not is_valid_domain(u_text):
                await message.reply("❌ Domain format galat hai (Example: linkshortify.com). Re-try:")
                return
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = {
                "state": "SET_SHORT_API",
                "domain": u_text,
                "prompt": await client.send_message(chat_id, "🔑 **Ab us website ki API Key bhejein:**")
            }
            return

        elif state == "SET_SHORT_API":
            if not is_valid_api(u_text):
                await message.reply("❌ Galat API key! Dobara bhejein:")
                return
            domain_name = current["domain"]
            await db.update_setting("shortlink_url", domain_name)
            await db.update_setting("shortlink_api", u_text)
            try: await prompt.delete(); await message.delete()
            except: pass
            ADMIN_STATES[admin_id] = None
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error processing state: {e}")
        ADMIN_STATES[admin_id] = None
