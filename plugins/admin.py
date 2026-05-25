import asyncio
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from plugins.dbusers import db  # Namespace issue se bachne ke liye explicit import
from utils import *
import pytz
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================
# 🧠 BOT KI NAYI MEMORY (Universal State Tracker)
# =============================================================
ADMIN_STATE = {}

# -------------------------------------------------------------
# HELPER VALIDATION & TIMER FUNCTIONS
# -------------------------------------------------------------
def is_valid_domain(domain):
    pattern = r"^(?!:\/\/)([a-zA-Z0-9-_]+\.)*[a-zA-Z0-9][a-zA-Z0-9-_]+\.[a-zA-Z]{2,11}$"
    return bool(re.match(pattern, domain.strip()))

def is_valid_api(api):
    api_clean = api.strip()
    if " " in api_clean or len(api_clean) < 8:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_\-]+$", api_clean))

async def auto_delete_message(msg, delay=120):
    """Message bhejta hai aur 120 seconds ke baad delete kar deta hai."""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

# Shared Inline Back Button layout for temporary success/cancel messages
TEMP_BACK_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("≤ BACK", callback_data="adm_temp_back")]])

# -------------------------------------------------------------
# 1. MAIN PANEL TEXT & KEYBOARD GENERATOR
# -------------------------------------------------------------
async def get_main_panel_layout(settings):
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    
    text = (
        "⚡ **BOT ADMIN CONTROL PANEL** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome back, Admin! Use the buttons below to configure and manage your bot settings instantly.\n"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗠𝗘𝗡𝗨", callback_data="adm_sub_verify")],
        [InlineKeyboardButton("⏱️ 𝗔𝗨𝗧𝗢 𝗗𝗘𝗟𝗘𝗧𝗘 𝗠𝗘𝗡𝗨", callback_data="adm_sub_delete")],
        [InlineKeyboardButton("🎨 𝗦𝗧𝗔𝗥𝗧 𝗠𝗘𝗡𝗨", callback_data="adm_sub_start_page")],
        [InlineKeyboardButton("👑 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗠𝗘𝗡𝗨", callback_data="adm_sub_premium")],
        [InlineKeyboardButton(f"🛡️ 𝗣𝗥𝗢𝗧𝗘𝗖𝗧 𝗖𝗢𝗡𝗧𝗘𝗡𝗧: {p_status}", callback_data="adm_toggle_protect")],
        [InlineKeyboardButton("Hᴏᴍᴇ", callback_data='start')]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 2. VERIFICATION & SWITCH SUB-MENU LAYOUT
# -------------------------------------------------------------
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
        [InlineKeyboardButton(f"𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗠𝗢𝗗𝗘: {v_status}", callback_data="adm_toggle_verify")],
        [InlineKeyboardButton(f"𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗠𝗢𝗗𝗘: {prem_mode_status}", callback_data="adm_toggle_premium_mode")],
        [InlineKeyboardButton("𝗦𝗘𝗧 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗧𝗜𝗠𝗘 🔑", callback_data="adm_set_token_time")],
        [InlineKeyboardButton("𝗦𝗘𝗧 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 $  𝗔𝗣𝗜 𝗜𝗗 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨", callback_data="adm_back_main")]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 3. AUTO DELETE SUB-MENU LAYOUT
# -------------------------------------------------------------
async def get_delete_menu_layout(settings):
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60
    
    text = (
        "⏱️ **AUTO DELETE CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ **Current Timer:** `{del_time} Minutes`"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"𝗔𝗨𝗧𝗢 𝗗𝗘𝗟𝗘𝗧𝗘 𝗠𝗢𝗗𝗘: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton("𝗦𝗘𝗧 𝗗𝗘𝗟𝗘𝗧𝗘 𝗧𝗜𝗠𝗘 ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨", callback_data="adm_back_main")]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 4. START PAGE SUB-MENU LAYOUT
# -------------------------------------------------------------
async def get_start_page_menu_layout(settings):
    has_photo = "🟢 Set (Custom)" if settings.get("start_photo") else "🔴 Not Set (Text Only)"
    has_text = "🟢 Custom Text Enabled" if settings.get("custom_start_text") else "⚪ Default Text Enabled"
    s_status = "🟢 ON (Blurred Image)" if settings.get("start_spoiler", False) else "🔴 OFF (Clear Image)"
    
    text = (
        "🎨 **START PAGE CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ **Start Photo Status:** `{settings.get('start_photo', 'None')}`\n"
        f"📝 **Start Text Status:** `{has_text}`\n"
        f"⚠️ **Spoiler Status:** `{s_status}`\n\n"
        "Aap niche diye gaye button se live /start command ke message, photo aur spoiler toggle badal sakte hain."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ 𝗦𝗘𝗧 𝗦𝗧𝗔𝗥𝗧 𝗧𝗘𝗫𝗧", callback_data="adm_set_start_txt")], 
        [InlineKeyboardButton("🗑️ 𝗥𝗘𝗦𝗘𝗧 𝗦𝗧𝗔𝗥𝗧 𝗧𝗘𝗫𝗧", callback_data="adm_reset_start_txt")],
        [InlineKeyboardButton("🖼️ 𝗦𝗘𝗧 𝗦𝗧𝗔𝗥𝗧 𝗣𝗛𝗢𝗧𝗢 (𝗨𝗥𝗟)", callback_data="adm_set_start_img")], 
        [InlineKeyboardButton("🗑️ 𝗥𝗘𝗠𝗢重𝗩𝗘 𝗦𝗧𝗔𝗥𝗧 𝗣𝗛𝗢𝗧𝗢", callback_data="adm_remove_start_img")],
        [InlineKeyboardButton(f"🎭 𝗦??𝗢𝗜𝗟𝗘𝗥 𝗠𝗢𝗗𝗘: {'🟢 ON' if settings.get('start_spoiler', False) else '🔴 OFF'}", callback_data="adm_toggle_spoiler")],
        [InlineKeyboardButton("𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨", callback_data="adm_back_main")]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 5. PREMIUM USER MANAGEMENT SUB-MENU LAYOUT
# -------------------------------------------------------------
async def get_premium_menu_layout(settings):
    try:
        users_list = await db.get_all_premium_users()
        total_premium = len(users_list)
    except Exception:
        total_premium = 0

    current_buy_link = settings.get("premium_buy_link", "https://t.me/HDFILM0900_BOT")

    text = (
        "👑 **PREMIUM USER CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Total Premium Users:** `{total_premium}`\n"
        f"🔗 **Current Buy Link:** `{current_buy_link}`\n\n"
        "Aap niche diye gaye inline buttons ka use karke kisi bhi user ki Telegram UID se use Premium add/remove kar sakte hain aur 'Buy Premium' Link setup kar sakte hain."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ 𝗔𝗗𝗗 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗨𝗦𝗘𝗥𝗦", callback_data="adm_add_prem")],
        [InlineKeyboardButton("🗑️ 𝗥𝗘𝗠𝗢𝗩𝗘 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗨𝗦𝗘𝗥𝗦", callback_data="adm_rem_prem")],
        [InlineKeyboardButton("📜 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗨𝗦𝗘𝗥𝗦 𝗟𝗜𝗦𝗧", callback_data="adm_list_prem")],
        [InlineKeyboardButton("🔘 𝗦𝗘𝗧 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗕𝗨𝗧𝗧𝗢𝗡 𝗟𝗜𝗡𝗞", callback_data="adm_set_buy_link")],
        [InlineKeyboardButton("𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨", callback_data="adm_back_main")]
    ])
    return text, keyboard


# 🛠️ Command Handler - /admin
@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    await message.reply_text(text, reply_markup=keyboard)

# 🌟 Start Command Callback
@Client.on_callback_query(filters.regex("open_admin_from_start"))
async def open_admin_from_start(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    keyboard.inline_keyboard[-1] = [InlineKeyboardButton("𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨", callback_data="start")]
    await query.message.edit_text(text, reply_markup=keyboard)


# 🕹️ Callback Query Router
@Client.on_callback_query(filters.regex(r"^adm_"))
async def admin_callback(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    action = query.data.replace("adm_", "")
    settings = await db.get_settings()
    chat_id = query.message.chat.id
    
    # --- NAVIGATION SWITCHES ---
    if action == "back_main":
        text, keyboard = await get_main_panel_layout(settings)
        if "🔙 Back to Home" in str(query.message.reply_markup):
            keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
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
        
    # --- NEW: BACK HANDLE FOR TEMPORARY MESSAGES ---
    elif action == "temp_back":
        try:
            await query.message.delete()
        except:
            pass
        text, keyboard = await get_main_panel_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    # --- TOGGLES ACTIONS (NO USER INPUT NEEDED) ---
    elif action == "toggle_verify":
        new_val = not settings.get("verify_mode", True)
        await db.update_setting("verify_mode", new_val)
        if new_val == True:
            await db.update_setting("premium_mode", False)
            await query.answer("Verification Mode ON & Premium Mode OFF! 🔄", show_alert=True)
        else:
            await query.answer("Verification Mode Updated! ✅")
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)

    elif action == "toggle_premium_mode":
        new_val = not settings.get("premium_mode", False)
        await db.update_setting("premium_mode", new_val)
        if new_val == True:
            await db.update_setting("verify_mode", False)
            await query.answer("Premium Mode ON & Verification OFF! 👑", show_alert=True)
        else:
            await query.answer("Premium Mode Updated! ✅")
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        
    elif action == "toggle_delete":
        new_val = not settings.get("auto_delete_mode", True)
        await db.update_setting("auto_delete_mode", new_val)
        await query.answer("Auto-Delete Mode Updated! ✅")
        settings = await db.get_settings()
        text, keyboard = await get_delete_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        
    elif action == "toggle_protect":
        new_val = not settings.get("protect_content", False)
        await db.update_setting("protect_content", new_val)
        await query.answer("Content Protection Updated! ✅")
        settings = await db.get_settings()
        text, keyboard = await get_main_panel_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)

    elif action == "toggle_spoiler":
        new_val = not settings.get("start_spoiler", False)
        await db.update_setting("start_spoiler", new_val)
        await query.answer(f"Spoiler Mode {'Enabled 🟢' if new_val else 'Disabled 🔴'}")
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)

    # --- RESET / LIST ACTIONS (NO USER INPUT NEEDED) ---
    elif action == "reset_start_txt":
        await db.update_setting("custom_start_text", None) 
        await query.answer("Start message default text par reset ho gaya! ⚪", show_alert=True)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)

    elif action == "remove_start_img":
        await db.update_setting("start_photo", None) 
        await query.answer("Start image successfully remove ho gayi! 🗑️", show_alert=True)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)

    elif action == "list_prem":
        try:
            users = await db.get_all_premium_users()
        except Exception:
            users = []
        if not users:
            list_text = "<b>ℹ️ Premium user list bilkul khali hai!</b>"
        else:
            list_text = "📜 **CURRENT PREMIUM USERS LIST**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for idx, u_id in enumerate(users, start=1):
                list_text += f"{idx}. 👤 ID: <code>{u_id}</code>\n"
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_sub_premium")]])
        await query.message.edit_text(text=list_text, reply_markup=back_keyboard)

    # =============================================================
    # 📝 ACTIONS REQUIRING USER INPUT
    # =============================================================
    elif action in ["add_prem", "rem_prem", "set_buy_link", "set_start_txt", "set_start_img", "set_time", "set_token_time", "change_link"]:
        await query.answer() 
        await query.message.delete()
        
        prompt_text = ""
        step = ""
        
        if action == "add_prem":
            prompt_text = "👑 **[Sᴛᴇᴘ 1/2] Sᴇɴᴅ Tʜᴇ Nᴇᴡ Pʀᴇᴍɪᴜᴍ Usᴇʀ's UID (Tᴇʟᴇɢʀᴀᴍ ID):**\n\n*(Oɴʟʏ Nᴜᴍʙᴇʀs Aʟʟᴏᴡᴇᴅ. Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ)*"
            step = "add_prem_id"
        elif action == "rem_prem":
            prompt_text = "🗑️ **Sᴇɴᴅ Tʜᴇ Usᴇʀ's UID Tᴏ Rᴇᴍᴏᴠᴇ Fʀᴏᴍ Pʀᴇᴍɪᴜᴍ:**\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ)*"
            step = "rem_prem_id"
        elif action == "set_buy_link":
            prompt_text = "🔗 **Sᴇɴᴅ Tʜᴇ Pʀᴇᴍɪᴜᴍ Pᴜʀᴄʜᴀsᴇ Lɪɴᴋ Fᴏʀ Usᴇʀs:**\n*(Ex: `https://t.me/your_username`)*\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ)*"
            step = "set_buy_link"
        elif action == "set_start_txt":
            prompt_text = "✍️ **Sᴇɴᴅ Tʜᴇ Nᴇᴡ /start Mᴇssᴀɢᴇ Tᴇxᴛ:**\n*(Yᴏᴜ Cᴀɴ Usᴇ HTML/Mᴀʀᴋᴅᴏᴡɴ Tᴀɢs)*\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ)*"
            step = "set_start_txt"
        elif action == "set_start_img":
            prompt_text = "🖼️ **Sᴇɴᴅ Tʜᴇ URL (Lɪɴᴋ) Oғ Tʜᴇ Nᴇᴡ Sᴛᴀʀᴛ Pʜᴏᴛᴏ:**\n*(Exᴀᴍᴘʟᴇ: `https://site.com/image.png`)*\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ)*"
            step = "set_start_img"
        elif action == "set_time":
            prompt_text = "⏱️ **Sᴇɴᴅ Tʜᴇ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ Tɪᴍᴇ Iɴ Mɪɴᴜᴛᴇs:**\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ Tʜᴇ Pʀᴏᴄᴇss)*"
            step = "set_delete_time"
        elif action == "set_token_time":
            prompt_text = "🔑 **Sᴇɴᴅ Tʜᴇ Tᴏᴋᴇɴ Vᴀʟɪᴅɪᴛʏ Tɪᴍᴇ Iɴ Hᴏᴜʀs:**\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ Tʜᴇ Pʀᴏᴄᴇss)*"
            step = "set_token_time"
        elif action == "change_link":
            prompt_text = "🔗 **Sᴇɴᴅ Tʜᴇ Nᴇᴡ Sʜᴏʀᴛᴇɴᴇʀ Dᴏᴍᴀɪɴ Nᴀᴍᴇ:**\n*(Exᴀᴍᴘʟᴇ: `site.com`)*\n\n*(Tʏᴘᴇ /cancel Tᴏ Cᴀɴᴄᴇʟ Tʜᴇ Pʀᴏᴄᴇss)*"
            step = "set_shortener_domain"


        ask_msg = await client.send_message(chat_id, prompt_text)
        ADMIN_STATE[chat_id] = {"step": step, "bot_msg_id": ask_msg.id}


# =============================================================
# 📡 UNIVERSAL MESSAGE LISTENER (With Layouts & 2 Min Auto Delete)
# =============================================================
@Client.on_message(filters.private & filters.text, group=1)
async def admin_state_listener(client: Client, message):
    chat_id = message.from_user.id
    
    if chat_id not in ADMIN_STATE:
        return
        
    state = ADMIN_STATE[chat_id]
    step = state["step"]
    
    # 🧹 User aur Bot ke purane questions messages delete karo
    try:
        await message.delete()
    except:
        pass

    if "bot_msg_id" in state:
        try:
            await client.delete_messages(chat_id, state["bot_msg_id"])
        except:
            pass

    text = message.text.strip()

    # ❌ CANCEL PROCESS
    if text == "/cancel":
        del ADMIN_STATE[chat_id]
        cancel_msg = await message.reply("**CANCELLED THIS PROCESS...**", reply_markup=TEMP_BACK_BTN)
        asyncio.create_task(auto_delete_message(cancel_msg, 120))
        return

    # ---------------------------------------------------------
    # 🟢 ADD PREMIUM STEPS
    # ---------------------------------------------------------
    if step == "add_prem_id":
        if not text.isdigit():
            err_msg = await message.reply("❌ **Invalid Format!** Kripya sirf numerical Telegram ID send karein (Cancel: /cancel).")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id
            return
            
        target_id = int(text)
        ADMIN_STATE[chat_id]["target_id"] = target_id
        ADMIN_STATE[chat_id]["step"] = "add_prem_days"
        
        ask_msg = await message.reply(f"⏱️ **[STEP 2/2] User `{target_id}` ko kitne DINO (Days) ke liye Premium banana hai?**\n*(Example: 30)*")
        ADMIN_STATE[chat_id]["bot_msg_id"] = ask_msg.id

    elif step == "add_prem_days":
        if not text.isdigit() or int(text) <= 0:
            err_msg = await message.reply("❌ **Invalid Days!** Kripya sirf positive number bhejiyega.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id
            return
            
        premium_days = int(text)
        target_id = ADMIN_STATE[chat_id]["target_id"]
        del ADMIN_STATE[chat_id] 
        
        expiry_date = await db.add_premium_user(target_id, premium_days)
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_expiry = expiry_date.replace(tzinfo=pytz.utc).astimezone(ist_timezone)
        formatted_expiry = ist_expiry.strftime('%Y-%m-%d %H:%M IST')
        
        # Screenshot jaisa simple text handle
        success_text = f"**Premium access added to the user with id -\n{target_id}.**"
        success_msg = await message.reply(success_text, reply_markup=TEMP_BACK_BTN)
        asyncio.create_task(auto_delete_message(success_msg, 120))
        
        try:
            await client.send_message(target_id, f"🎉 **CONGRATULATIONS !!**\nAapke Account par **{premium_days} Dino** ke liye **👑 PREMIUM ACCESS** active kar diya gaya hai!\n📅 **Expiry Date:** `{formatted_expiry}`")
        except Exception as e:
            logger.error(f"Failed to notify user {target_id}: {e}")

    # ---------------------------------------------------------
    # 🔴 REMOVE PREMIUM
    # ---------------------------------------------------------
    elif step == "rem_prem_id":
        if not text.isdigit():
            err_msg = await message.reply("❌ **Invalid Format!** Kripya sirf numerical Telegram ID send karein.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id
            return
            
        target_id = int(text)
        del ADMIN_STATE[chat_id]
        is_removed = await db.remove_premium_user(target_id)
        
        if is_removed:
            success_msg = await message.reply(f"**Premium access removed for user id -\n{target_id}.**", reply_markup=TEMP_BACK_BTN)
            try:
                await client.send_message(target_id, "⚠️ **PREMIUM PLAN EXPIRED / REMOVED**\nAapke account se Premium Access hata diya gaya hai.")
            except:
                pass
        else:
            success_msg = await message.reply(f"❌ **User ID {target_id} Premium list mein nahi mila.**", reply_markup=TEMP_BACK_BTN)
            
        asyncio.create_task(auto_delete_message(success_msg, 120))

    # ---------------------------------------------------------
    # 🔗 SET BUY LINK
    # ---------------------------------------------------------
    elif step == "set_buy_link":
        del ADMIN_STATE[chat_id]
        await db.update_setting("premium_buy_link", text)
        success_msg = await message.reply(f"✅ **Premium Buy Link updated successfully!**", reply_markup=TEMP_BACK_BTN)
        asyncio.create_task(auto_delete_message(success_msg, 120))

    # ---------------------------------------------------------
    # ✍️ SET START TEXT
    # ---------------------------------------------------------
    elif step == "set_start_txt":
        del ADMIN_STATE[chat_id]
        await db.update_setting("custom_start_text", text)
        success_msg = await message.reply("✅ **Start page message text update ho gaya!**", reply_markup=TEMP_BACK_BTN)
        asyncio.create_task(auto_delete_message(success_msg, 120))

    # ---------------------------------------------------------
    # 🖼️ SET START PHOTO (URL BASED CHANGE)
    # ---------------------------------------------------------
    elif step == "set_start_img":
        if not text.startswith(("http://", "https://")):
            err_msg = await message.reply("❌ **Invalid Format!** Kripya ek valid Image URL/Link bhejein.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id
            return
            
        del ADMIN_STATE[chat_id]
        await db.update_setting("start_photo", text)
        success_msg = await message.reply("✅ **Start Page Image URL updated successfully!**", reply_markup=TEMP_BACK_BTN)
        asyncio.create_task(auto_delete_message(success_msg, 120))

    # ---------------------------------------------------------
    # ⏱️ SET DELETE TIME
    # ---------------------------------------------------------
    elif step == "set_delete_time":
        try:
            minutes = int(text)
            del ADMIN_STATE[chat_id]
            await db.update_setting("auto_delete_time", minutes * 60)
            success_msg = await message.reply(f"✅ **Auto-Delete timer set to {minutes} Minutes!**", reply_markup=TEMP_BACK_BTN)
            asyncio.create_task(auto_delete_message(success_msg, 120))
        except ValueError:
            err_msg = await message.reply("❌ **Invalid Format!** Only clean numbers (minutes) are allowed.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id

    # ---------------------------------------------------------
    # 🔑 SET TOKEN TIME
    # ---------------------------------------------------------
    elif step == "set_token_time":
        try:
            hours = int(text)
            del ADMIN_STATE[chat_id]
            await db.update_setting("verify_expire_time", hours * 3600)
            success_msg = await message.reply(f"✅ **Token validity set to {hours} Hours!**", reply_markup=TEMP_BACK_BTN)
            asyncio.create_task(auto_delete_message(success_msg, 120))
        except ValueError:
            err_msg = await message.reply("❌ **Invalid Format!** Only integers/numbers (hours) are allowed.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id

    # ---------------------------------------------------------
    # 🔗 SET SHORTENER (DOMAIN -> API)
    # ---------------------------------------------------------
    elif step == "set_shortener_domain":
        if not is_valid_domain(text):
            err_msg = await message.reply("❌ **Invalid Domain Format!** Use explicit domain formats like `site.com`.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id
            return
            
        ADMIN_STATE[chat_id]["domain"] = text
        ADMIN_STATE[chat_id]["step"] = "set_shortener_api"
        
        ask_msg = await message.reply("🔑 **Us Website ki API Key bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*")
        ADMIN_STATE[chat_id]["bot_msg_id"] = ask_msg.id

    elif step == "set_shortener_api":
        if not is_valid_api(text):
            err_msg = await message.reply("❌ **Invalid API Format!**\nAPI strings should contain no spaces.")
            ADMIN_STATE[chat_id]["bot_msg_id"] = err_msg.id
            return
            
        domain = ADMIN_STATE[chat_id]["domain"]
        api = text
        del ADMIN_STATE[chat_id]
        
        await db.update_setting("shortlink_url", domain)
        await db.update_setting("shortlink_api", api)
        
        success_msg = await message.reply("✅ **Shortener Details Updated Successfully!**", reply_markup=TEMP_BACK_BTN)
        asyncio.create_task(auto_delete_message(success_msg, 120))
