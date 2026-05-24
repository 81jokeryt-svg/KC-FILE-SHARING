import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from plugins.dbusers import *
from utils import *

# -------------------------------------------------------------
# HELPER VALIDATION FUNCTIONS
# -------------------------------------------------------------
def is_valid_domain(domain):
    # Regex to check valid domain format (e.g., shortener.com, api.link.in)
    pattern = r"^(?!:\/\/)([a-zA-Z0-9-_]+\.)*[a-zA-Z0-9][a-zA-Z0-9-_]+\.[a-zA-Z]{2,11}$"
    return bool(re.match(pattern, domain.strip()))

def is_valid_api(api):
    # API tokens shouldn't have spaces and usually match standard hex/alphanumeric formats length >= 8
    api_clean = api.strip()
    if " " in api_clean or len(api_clean) < 8:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_\-]+$", api_clean))


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
        [InlineKeyboardButton("🔐 VERIFICATION MENU", callback_data="adm_sub_verify")],
        [InlineKeyboardButton("⏱️ AUTO DELETE MENU", callback_data="adm_sub_delete")],
        [InlineKeyboardButton(f"🛡️ PROTECT CONTENT: {p_status}", callback_data="adm_toggle_protect")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_data")]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 2. VERIFICATION SUB-MENU LAYOUT
# -------------------------------------------------------------
async def get_verify_menu_layout(settings):
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    v_expire_hours = settings.get("verify_expire_time", 86400) // 3600
    
    text = (
        "🔐 **VERIFICATION CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **Shortener Site:** `{settings.get('shortlink_url')}`\n"
        f"🔑 **Shortener API:** `{settings.get('shortlink_api')}`\n"
        f"⏱️ **Token Validity:** `{v_expire_hours} Hours`"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification Mode: {v_status}", callback_data="adm_toggle_verify")],
        [InlineKeyboardButton("Set Token Validity 🔑", callback_data="adm_set_token_time")],
        [InlineKeyboardButton("Change Shortener Link & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
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
        [InlineKeyboardButton(f"Auto Delete Mode: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton("Set Delete Timer ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
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
    keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
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

    # --- TOGGLES ACTIONS ---
    elif action == "toggle_verify":
        new_val = not settings.get("verify_mode", True)
        await db.update_setting("verify_mode", new_val)
        await query.answer("Verification Mode Updated! ✅")
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
        if "🔙 Back to Home" in str(query.message.reply_markup):
            keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
        await query.message.edit_text(text, reply_markup=keyboard)
        
    # --- DYNAMIC INPUT SETTINGS WITH VALIDATION & CANCEL FEATURE ---
    elif action == "set_time":
        await query.message.delete()
        time_msg = await client.ask(chat_id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        
        if time_msg.text.strip() == "/cancel":
            cancel_msg = await client.send_message(chat_id, "❌ Process Cancelled!")
            await asyncio.sleep(2)
            await cancel_msg.delete()
            await time_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_delete_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        try:
            minutes = int(time_msg.text.strip())
            await db.update_setting("auto_delete_time", minutes * 60)
            success_msg = await client.send_message(chat_id, f"✅ Auto-Delete timer set to **{minutes} Minutes**!")
        except ValueError:
            success_msg = await client.send_message(chat_id, "❌ Invalid Format! Sirf numbers allowed hain.")
        
        await asyncio.sleep(3)
        await success_msg.delete()
        await time_msg.delete()
        
        settings = await db.get_settings()
        text, keyboard = await get_delete_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "set_token_time":
        await query.message.delete()
        time_msg = await client.ask(chat_id, "🔑 **Token Validity ka time Hours (Ghante) me bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        
        if time_msg.text.strip() == "/cancel":
            cancel_msg = await client.send_message(chat_id, "❌ Process Cancelled!")
            await asyncio.sleep(2)
            await cancel_msg.delete()
            await time_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        try:
            hours = int(time_msg.text.strip())
            await db.update_setting("verify_expire_time", hours * 3600)
            success_msg = await client.send_message(chat_id, f"✅ Token validity set to **{hours} Hours**!")
        except ValueError:
            success_msg = await client.send_message(chat_id, "❌ Invalid Format! Sirf numbers allowed hain.")
            
        await asyncio.sleep(3)
        await success_msg.delete()
        await time_msg.delete()
        
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "change_link":
        await query.message.delete()
        
        # 1. Ask Domain
        site_msg = await client.ask(chat_id, "🔗 **Naya Shortener Domain name bhejein:**\n*(Example: `linkshortify.com`)*\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        new_site = site_msg.text.strip()
        
        if new_site == "/cancel":
            cancel_msg = await client.send_message(chat_id, "❌ Process Cancelled!")
            await asyncio.sleep(2)
            await cancel_msg.delete()
            await site_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not is_valid_domain(new_site):
            err_msg = await client.send_message(chat_id, "❌ **Invalid Domain Format!**\nKripya sahi text format provide karein (e.g., `site.com` ya `api.cc`).")
            await asyncio.sleep(4)
            await err_msg.delete()
            await site_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        # 2. Ask API
        api_msg = await client.ask(chat_id, "🔑 **Us Website ki API Key bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        new_api = api_msg.text.strip()
        
        if new_api == "/cancel":
            cancel_msg = await client.send_message(chat_id, "❌ Process Cancelled!")
            await asyncio.sleep(2)
            await cancel_msg.delete()
            await site_msg.delete()
            await api_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not is_valid_api(new_api):
            err_msg = await client.send_message(chat_id, "❌ **Invalid API Format!**\nAPI key me spaces nahi hone chahiye aur length minimum 8 chars honi chahiye.")
            await asyncio.sleep(4)
            await err_msg.delete()
            await site_msg.delete()
            await api_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return
        
        # Save validated results
        await db.update_setting("shortlink_url", new_site)
        await db.update_setting("shortlink_api", new_api)
        
        success_msg = await client.send_message(chat_id, "✅ **Shortener Details Updated Successfully!**")
        await asyncio.sleep(3)
        await success_msg.delete()
        await site_msg.delete()
        await api_msg.delete()
        
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return
