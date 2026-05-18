# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from plugins.dbusers import db  # Database mapping module
from utils import generate_settings_keyboard 
from config import ADMIN  # Config se ADMIN ID import ki global control ke liye

@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client, message):
    user_id = message.from_user.id
    
    # 🌟 ADMIN SECURITY CHECK: Normal user settings open nahi kar payega
    if user_id != ADMIN:
        return await message.reply_text(
            text="<b>❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!\n\nYeh settings menu sirf Bot Owner/Admin ke liye hai. Aap isme badlaav nahi kar sakte.</b>",
            protect_content=True
        )
    
    # Central database se hamesha Global settings fetch hogi
    user_settings = await db.get_user_settings(ADMIN)
    
    # Venom wala duplicate design yahan se saaf kar diya hai
    text = (
        "⚙️ **WELCOME TO GLOBAL CONTROL PANEL**\n\n"
        "Yahan se aap jo bhi toggle change karenge, wo instantly poore bot ke sabhi users par apply ho jayega."
    )
    await message.reply_text(text, reply_markup=generate_settings_keyboard(user_settings))


@Client.on_callback_query(filters.regex(r"^toggle_"))
async def toggle_settings_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # 🌟 BUTTON SECURITY LAYER: Koi user hacker banne ki koshish kare toh block ho
    if user_id != ADMIN:
        return await callback_query.answer(
            text="❌ Warning: Aapke paas is setting ko badalane ki permission nahi hai!", 
            show_alert=True
        )
        
    setting_key = callback_query.data.replace("toggle_", "")
    
    # 1. Database se Global settings fetch karein (ADMIN context)
    current_settings = await db.get_user_settings(ADMIN)
    
    # 2. Toggle state inversion logic
    new_value = not current_settings.get(setting_key, False)
    
    # 3. MongoDB permanent global collection update
    await db.update_user_setting(ADMIN, setting_key, new_value)
    
    # 4. Local dict state match reference (for instant UI render loop)
    current_settings[setting_key] = new_value
    
    status_str = "ENABLED ✅" if new_value else "DISABLED ❌"
    clean_name = setting_key.replace('_', ' ').title()
    await callback_query.answer(f"{clean_name} is now {status_str}", show_alert=False)
    
    # Re-render system with live updated cursor state database 
    await callback_query.message.edit_reply_markup(
        reply_markup=generate_settings_keyboard(current_settings)
    )
