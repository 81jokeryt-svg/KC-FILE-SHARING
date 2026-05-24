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
    pattern = r"^(?!:\/\/)([a-zA-Z0-9-_]+\.)*[a-zA-Z0-9][a-zA-Z0-9-_]+\.[a-zA-Z]{2,11}$"
    return bool(re.match(pattern, domain.strip()))

def is_valid_api(api):
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
        [InlineKeyboardButton("🎨 START PAGE CUSTOMIZER", callback_data="adm_sub_start_page")],
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

# -------------------------------------------------------------
# 4. START PAGE SUB-MENU LAYOUT (NEWLY ADDED)
# -------------------------------------------------------------
async def get_start_page_menu_layout(settings):
    has_photo = "🟢 Set (Custom)" if settings.get("start_photo") else "🔴 Not Set (Text Only)"
    has_text = "🟢 Custom Text Enabled" if settings.get("start_text") else "⚪ Default Text Enabled"
    
    text = (
        "🎨 **START PAGE CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ **Start Photo Status:** `{has_photo}`\n"
        f"📝 **Start Text Status:** `{has_text}`\n\n"
        "Aap niche diye gaye button se live /start command ke message aur photo badal sakte hain."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Set Start Text", callback_data="adm_set_start_txt"), 
         InlineKeyboardButton("🗑️ Reset Start Text", callback_data="adm_reset_start_txt")],
        [InlineKeyboardButton("🖼️ Set Start Photo", callback_data="adm_set_start_img"), 
         InlineKeyboardButton("🗑️ Remove Start Photo", callback_data="adm_remove_start_img")],
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
        
    elif action == "sub_start_page":
        text, keyboard = await get_start_page_menu_layout(settings)
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

    # =============================================================
    # --- START PAGE CONTROL ACTIONS (TEXT & IMAGE SET/REMOVE) ---
    # =============================================================
    elif action == "set_start_txt":
        await query.message.delete()
        txt_prompt = await client.ask(chat_id, "✍️ **Naya /start message text likh kar bhejein:**\n\n*(HTML/Markdown tags use kar sakte hain. Cancel karne ke liye /cancel likhein)*", filters=filters.text)
        
        if txt_prompt.text.strip() == "/cancel":
            await txt_prompt.delete()
            settings = await db.get_settings()
            text, keyboard = await get_start_page_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        await db.update_setting("start_text", txt_prompt.text.strip())
        success_msg = await client.send_message(chat_id, "✅ **Start page message text update ho gaya!**")
        await asyncio.sleep(3)
        await success_msg.delete()
        await txt_prompt.delete()
        
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "reset_start_txt":
        await db.update_setting("start_text", None) # None karne par default state par chala jayega
        await query.answer("Start message default text par reset ho gaya! ⚪", show_alert=True)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    elif action == "set_start_img":
        await query.message.delete()
        img_prompt = await client.ask(chat_id, "🖼️ **Nayi Start Photo ya image file bhejein (As a Photo):**\n\n*(Cancel karne ke liye /cancel text likh kar send karein)*")
        
        if img_prompt.text and img_prompt.text.strip() == "/cancel":
            await img_prompt.delete()
            settings = await db.get_settings()
            text, keyboard = await get_start_page_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not img_prompt.photo:
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_start_page")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Kripya sirf ek image/photo forward ya upload karein.", reply_markup=back_keyboard)
            return
            
        # Extract highest quality photo file_id string
        file_id = img_prompt.photo.file_id
        await db.update_setting("start_photo", file_id)
        
        success_msg = await client.send_message(chat_id, "✅ **Start Page Image updated successfully!**")
        await asyncio.sleep(3)
        await success_msg.delete()
        await img_prompt.delete()
        
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "remove_start_img":
        await db.update_setting("start_photo", None) # Database me clear control string save karega
        await query.answer("Start image successfully remove ho gayi! (Text-Only Mode Enabled) 🗑️", show_alert=True)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    # --- EXISTING VALIDATION CONTROLS ---
    elif action == "set_time":
        await query.message.delete()
        time_msg = await client.ask(chat_id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        
        if time_msg.text.strip() == "/cancel":
            await time_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_delete_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        try:
            minutes = int(time_msg.text.strip())
            await db.update_setting("auto_delete_time", minutes * 60)
            success_msg = await client.send_message(chat_id, f"✅ Auto-Delete timer set to **{minutes} Minutes**!")
            await asyncio.sleep(3)
            await success_msg.delete()
            await time_msg.delete()
            
            settings = await db.get_settings()
            text, keyboard = await get_delete_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
        except ValueError:
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_delete")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Only clean numbers are allowed.", reply_markup=back_keyboard)
        return

    elif action == "set_token_time":
        await query.message.delete()
        time_msg = await client.ask(chat_id, "🔑 **Token Validity ka time Hours (Ghante) me bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        
        if time_msg.text.strip() == "/cancel":
            await time_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        try:
            hours = int(time_msg.text.strip())
            await db.update_setting("verify_expire_time", hours * 3600)
            success_msg = await client.send_message(chat_id, f"✅ Token validity set to **{hours} Hours**!")
            await asyncio.sleep(3)
            await success_msg.delete()
            await time_msg.delete()
            
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
        except ValueError:
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_verify")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Only integers/numbers are allowed.", reply_markup=back_keyboard)
        return

    elif action == "change_link":
        await query.message.delete()
        
        site_msg = await client.ask(chat_id, "🔗 **Naya Shortener Domain name bhejein:**\n*(Example: `linkshortify.com`)*\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        new_site = site_msg.text.strip()
        
        if new_site == "/cancel":
            await site_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not is_valid_domain(new_site):
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_verify")]])
            await client.send_message(chat_id, "❌ **Invalid Domain Format!**\nUse explicit domain formats like `site.com` or `api.cc` without protocols.", reply_markup=back_keyboard)
            return

        api_msg = await client.ask(chat_id, "🔑 **Us Website ki API Key bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*", filters=filters.text)
        new_api = api_msg.text.strip()
        
        if new_api == "/cancel":
            await site_msg.delete()
            await api_msg.delete()
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not is_valid_api(new_api):
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_verify")]])
            await client.send_message(chat_id, "❌ **Invalid API Format!**\nAPI strings should contain no spaces and contain valid alphanumeric sequences.", reply_markup=back_keyboard)
            return
        
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
