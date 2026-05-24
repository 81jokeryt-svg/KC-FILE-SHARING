import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from dbusers import db  # Agar aapki DB file ka naam alag hai to modify karein

# 🛠️ Command to open Admin Panel
@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    settings = await db.get_settings()
    
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60 # Convert to minutes
    
    text = f"""⚙️ **BOT ADMIN PANEL** ⚙️

Yahan se aap bina deploy kiye bot ki live variables set kar sakte hain:

🔗 **Shortener Site:** `{settings.get('shortlink_url')}`
🔑 **Shortener API:** `{settings.get('shortlink_api')}`
⏱️ **Auto-Delete Time:** `{del_time} Minutes`"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Verification: {v_status}", callback_data="adm_toggle_verify"),
            InlineKeyboardButton(f"Auto Delete: {d_status}", callback_data="adm_toggle_delete")
        ],
        [
            InlineKeyboardButton(f"Forward Protect: {p_status}", callback_data="adm_toggle_protect"),
            InlineKeyboardButton("Set Delete Time ⏱️", callback_data="adm_set_time")
        ],
        [
            InlineKeyboardButton("Change Shortener Site & API 🔗", callback_data="adm_change_link")
        ],
        [
            InlineKeyboardButton("❌ Close Panel", callback_data="adm_close")
        ]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)


# 🕹️ Processing Panel Button Clicks
@Client.on_callback_query(filters.regex(r"^adm_") & filters.user(ADMINS))
async def admin_callback(client, query):
    action = query.data.replace("adm_", "")
    settings = await db.get_settings()
    
    if action == "close":
        await query.message.delete()
        return
        
    elif action == "toggle_verify":
        new_val = not settings.get("verify_mode", True)
        await db.update_setting("verify_mode", new_val)
        await query.answer(f"Verification {'Enabled' if new_val else 'Disabled'}!")
        
    elif action == "toggle_delete":
        new_val = not settings.get("auto_delete_mode", True)
        await db.update_setting("auto_delete_mode", new_val)
        await query.answer(f"Auto-Delete {'Enabled' if new_val else 'Disabled'}!")
        
    elif action == "toggle_protect":
        new_val = not settings.get("protect_content", False)
        await db.update_setting("protect_content", new_val)
        await query.answer(f"Forward Protection {'Enabled' if new_val else 'Disabled'}!")
        
    elif action == "set_time":
        await query.message.delete()
        # Admin se reply mangna time badalne ke liye
        time_msg = await client.ask(query.message.chat.id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n*(Example: Agat 5 minute set karna hai to sirf 5 likhein)*")
        try:
            minutes = int(time_msg.text)
            seconds = minutes * 60
            await db.update_setting("auto_delete_time", seconds)
            await client.send_message(query.message.chat.id, f"✅ Auto-Delete time badal kar **{minutes} Minutes** kar diya gaya hai! Dubara /admin type karein.")
        except ValueError:
            await client.send_message(query.message.chat.id, "❌ Invalid format! Sirf number bhejna tha.")
        return

    elif action == "change_link":
        await query.message.delete()
        # Domain set karna
        site_msg = await client.ask(query.message.chat.id, "🔗 **Naya Shortener Domain name bhejein:**\n*(Example: linkshortify.com)*")
        new_site = site_msg.text.strip()
        
        # API key set karna
        api_msg = await client.ask(query.message.chat.id, "🔑 **Us Website ki API Key bhejein:**")
        new_api = api_msg.text.strip()
        
        await db.update_setting("shortlink_url", new_site)
        await db.update_setting("shortlink_api", new_api)
        await client.send_message(query.message.chat.id, f"✅ Shortener Details Update Ho Gayi Hain!\n\n**Site:** {new_site}\n**API:** {new_api}\n\nCheck karne ke liye fir se /admin type karein.")
        return

    # Panel refresh mechanism
    settings = await db.get_settings()
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60
    
    text = f"⚙️ **BOT ADMIN PANEL** ⚙️\n\nYahan se aap bina deploy kiye bot ki live variables set kar sakte hain:\n\n🔗 **Shortener Site:** `{settings.get('shortlink_url')}`\n🔑 **Shortener API:** `{settings.get('shortlink_api')}`\n⏱️ **Auto-Delete Time:** `{del_time} Minutes`"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification: {v_status}", callback_data="adm_toggle_verify"), InlineKeyboardButton(f"Auto Delete: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton(f"Forward Protect: {p_status}", callback_data="adm_toggle_protect"), InlineKeyboardButton("Set Delete Time ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("Change Shortener Site & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="adm_close")]
    ])
    
    await query.message.edit_text(text, reply_markup=keyboard)
