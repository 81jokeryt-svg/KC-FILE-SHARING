from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from plugins.dbusers import db  # Database mapping module import kiya
from utils import generate_settings_keyboard 

@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client, message):
    user_id = message.from_user.id
    
    # Live fetch database user current states
    user_settings = await db.get_user_settings(user_id)
    
    text = (
        "╔════════════════════════╗\n"
        "🎬   **VENOM FILE STORE BOT**\n"
        "╚════════════════════════╝\n\n"
        "⚙️ **HERE IS THE SETTINGS MENU**\n"
        "Customize your settings as per your need."
    )
    await message.reply_text(text, reply_markup=generate_settings_keyboard(user_settings))


@Client.on_callback_query(filters.regex(r"^toggle_"))
async def toggle_settings_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    setting_key = callback_query.data.replace("toggle_", "")
    
    # 1. Database se settings fetch karein
    current_settings = await db.get_user_settings(user_id)
    
    # 2. Toggle state logic
    new_value = not current_settings.get(setting_key, False)
    
    # 3. MongoDB permanent collections table cluster update
    await db.update_user_setting(user_id, setting_key, new_value)
    
    # 4. Local dict state match reference (for instant UI render loop)
    current_settings[setting_key] = new_value
    
    status_str = "ENABLED ✅" if new_value else "DISABLED ❌"
    clean_name = setting_key.replace('_', ' ').title()
    await callback_query.answer(f"{clean_name} is now {status_str}", show_alert=False)
    
    # Re-render system with live updated cursor state database 
    await callback_query.message.edit_reply_markup(
        reply_markup=generate_settings_keyboard(current_settings)
    )
