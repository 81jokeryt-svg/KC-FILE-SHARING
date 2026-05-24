import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from plugins.dbusers import *
from utils import *

# -------------------------------------------------------------
# 1. MAIN PANEL TEXT & KEYBOARD GENERATOR (3 MAIN BUTTONS + CLOSE)
# -------------------------------------------------------------
async def get_main_panel_layout(settings):
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    
    text = "⚙️ **BOT ADMIN PANEL** ⚙️\n\nWelcome back Admin! Bot ke settings ko manage karne ke liye niche diye gaye kisi bhi menu par click karein:"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 VERIFICATION MENU", callback_data="adm_sub_verify")],
        [InlineKeyboardButton("⏱️ AUTO DELETE MENU", callback_data="adm_sub_delete")],
        [InlineKeyboardButton(f"🛡️ CONTENT PROTECTION: {p_status}", callback_data="adm_toggle_protect")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_data")]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 2. VERIFICATION SUB-MENU LAYOUT
# -------------------------------------------------------------
async def get_verify_menu_layout(settings):
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    v_expire_hours = settings.get("verify_expire_time", 86400) // 3600
    
    text = f"""🔐 **VERIFICATION SETTINGS MENU**

Current Config:
🔗 **Shortener Site:** `{settings.get('shortlink_url')}`
🔑 **Shortener API:** `{settings.get('shortlink_api')}`
⏱️ **Token Validity Time:** `{v_expire_hours} Hours`"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification Toggle: {v_status}", callback_data="adm_toggle_verify")],
        [InlineKeyboardButton("Set Token Validity 🔑", callback_data="adm_set_token_time")],
        [InlineKeyboardButton("Change Shortener Site & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
    ])
    return text, keyboard

# -------------------------------------------------------------
# 3. AUTO DELETE SUB-MENU LAYOUT
# -------------------------------------------------------------
async def get_delete_menu_layout(settings):
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60
    
    text = f"""⏱️ **AUTO DELETE MENU**

Current Config:
⏱️ **Auto-Delete Time:** `{del_time} Minutes`"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Auto Delete Toggle: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton("Set Delete Time ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
    ])
    return text, keyboard


# 🛠️ Command Handler - /admin command chalane par
@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    await message.reply_text(text, reply_markup=keyboard)


# 🌟 Start Command Ke Button Se Main Admin Panel Kholna
@Client.on_callback_query(filters.regex("open_admin_from_start"))
async def open_admin_from_start(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    # Agar start page se aaya hai toh close button ko Back to Home kar denge
    keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
    await query.message.edit_text(text, reply_markup=keyboard)


# 🕹️ Callback Query Router (Saare button clicks handle karne ke liye)
@Client.on_callback_query(filters.regex(r"^adm_"))
async def admin_callback(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    action = query.data.replace("adm_", "")
    settings = await db.get_settings()
    
    # --- NAVIGATION SWITCHES (MENUS & BACK BUTTONS) ---
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

    # --- TOGGLES & SETTINGS ACTIONS ---
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
        
    elif action == "set_time":
        await query.message.delete()
        time_msg = await client.ask(query.message.chat.id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n*(Example: sirf 5 likhein)*")
        try:
            minutes = int(time_msg.text)
            await db.update_setting("auto_delete_time", minutes * 60)
            await client.send_message(query.message.chat.id, f"✅ Auto-Delete set to **{minutes} Minutes**! Dubara panel kholne ke liye /admin likhein.")
        except:
            await client.send_message(query.message.chat.id, "❌ Invalid Format!")
        return

    elif action == "set_token_time":
        await query.message.delete()
        time_msg = await client.ask(query.message.chat.id, "🔑 **Token Validity ka time Hours (Ghante) me bhejein:**\n*(Example: sirf 24 likhein)*")
        try:
            hours = int(time_msg.text)
            await db.update_setting("verify_expire_time", hours * 3600)
            await client.send_message(query.message.chat.id, f"✅ Token validity set to **{hours} Hours**! Dubara panel kholne ke liye /admin likhein.")
        except:
            await client.send_message(query.message.chat.id, "❌ Invalid Format!")
        return

    elif action == "change_link":
        await query.message.delete()
        site_msg = await client.ask(query.message.chat.id, "🔗 **Naya Shortener Domain name bhejein:**\n*(Example: linkshortify.com)*")
        new_site = site_msg.text.strip()
        api_msg = await client.ask(query.message.chat.id, "🔑 **Us Website ki API Key bhejein:**")
        new_api = api_msg.text.strip()
        
        await db.update_setting("shortlink_url", new_site)
        await db.update_setting("shortlink_api", new_api)
        await client.send_message(query.message.chat.id, "✅ Shortener Details Updated! Dubara panel kholne ke liye /admin likhein.")
        return
