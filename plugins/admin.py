import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from plugins.dbusers import *
from utils import *

# 🕹️ Command se admin panel open karne ka code
@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    settings = await db.get_settings()
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60 
    v_expire_hours = settings.get("verify_expire_time", 86400) // 3600
    
    text = f"⚙️ **BOT ADMIN PANEL** ⚙️\n\nYahan se aap bina deploy kiye bot ki live variables set kar sakte hain:\n\n🔗 **Shortener Site:** `{settings.get('shortlink_url')}`\n🔑 **Shortener API:** `{settings.get('shortlink_api')}`\n⏱️ **Auto-Delete Time:** `{del_time} Minutes`\n⏱️ **Token Validity Time:** `{v_expire_hours} Hours`"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification: {v_status}", callback_data="adm_toggle_verify"), InlineKeyboardButton(f"Auto Delete: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton(f"Forward Protect: {p_status}", callback_data="adm_toggle_protect"), InlineKeyboardButton("Set Delete Time ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("Set Token Validity 🔑", callback_data="adm_set_token_time"), InlineKeyboardButton("Change Shortener Site & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_data")]
    ])
    await message.reply_text(text, reply_markup=keyboard)


# 🌟 Home Page button click click logic with security barrier
@Client.on_callback_query(filters.regex("open_admin_from_start"))
async def open_admin_from_start(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return
        
    settings = await db.get_settings()
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60
    v_expire_hours = settings.get("verify_expire_time", 86400) // 3600
    
    text = f"⚙️ **BOT ADMIN PANEL** ⚙️\n\nYahan se aap bina deploy kiye bot ki live variables set kar sakte hain:\n\n🔗 **Shortener Site:** `{settings.get('shortlink_url')}`\n🔑 **Shortener API:** `{settings.get('shortlink_api')}`\n⏱️ **Auto-Delete Time:** `{del_time} Minutes`\n⏱️ **Token Validity Time:** `{v_expire_hours} Hours`"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification: {v_status}", callback_data="adm_toggle_verify"), InlineKeyboardButton(f"Auto Delete: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton(f"Forward Protect: {p_status}", callback_data="adm_toggle_protect"), InlineKeyboardButton("Set Delete Time ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("Set Token Validity 🔑", callback_data="adm_set_token_time"), InlineKeyboardButton("Change Shortener Site & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard)


# 🕹️ Processing Admin settings modifications
@Client.on_callback_query(filters.regex(r"^adm_"))
async def admin_callback(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    action = query.data.replace("adm_", "")
    settings = await db.get_settings()
    
    if action == "toggle_verify":
        new_val = not settings.get("verify_mode", True)
        await db.update_setting("verify_mode", new_val)
        await query.answer("Verification Mode Updated! ✅")
        
    elif action == "toggle_delete":
        new_val = not settings.get("auto_delete_mode", True)
        await db.update_setting("auto_delete_mode", new_val)
        await query.answer("Auto-Delete Mode Updated! ✅")
        
    elif action == "toggle_protect":
        new_val = not settings.get("protect_content", False)
        await db.update_setting("protect_content", new_val)
        await query.answer("Forward Protection Updated! ✅")
        
    elif action == "set_time":
        await query.message.delete()
        time_msg = await client.ask(query.message.chat.id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n*(Example: sirf 5 likhein)*")
        try:
            minutes = int(time_msg.text)
            await db.update_setting("auto_delete_time", minutes * 60)
            await client.send_message(query.message.chat.id, f"✅ Auto-Delete set to **{minutes} Minutes**! Re-open panel.")
        except:
            await client.send_message(query.message.chat.id, "❌ Invalid Format!")
        return

    elif action == "set_token_time":
        await query.message.delete()
        time_msg = await client.ask(query.message.chat.id, "🔑 **Token Validity ka time Hours (Ghante) me bhejein:**\n*(Example: sirf 24 likhein)*")
        try:
            hours = int(time_msg.text)
            await db.update_setting("verify_expire_time", hours * 3600)
            await client.send_message(query.message.chat.id, f"✅ Token validity set to **{hours} Hours**! Re-open panel.")
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
        await client.send_message(query.message.chat.id, "✅ Shortener Details Updated!")
        return

    # Dynamic panel refresh layout
    settings = await db.get_settings()
    v_status = "🟢 ON" if settings.get("verify_mode", True) else "🔴 OFF"
    d_status = "🟢 ON" if settings.get("auto_delete_mode", True) else "🔴 OFF"
    p_status = "🟢 ON" if settings.get("protect_content", False) else "🔴 OFF"
    del_time = settings.get("auto_delete_time", 1800) // 60
    v_expire_hours = settings.get("verify_expire_time", 86400) // 3600
    
    text = f"⚙️ **BOT ADMIN PANEL** ⚙️\n\nYahan se aap bina deploy kiye bot ki live variables set kar sakte hain:\n\n🔗 **Shortener Site:** `{settings.get('shortlink_url')}`\n🔑 **Shortener API:** `{settings.get('shortlink_api')}`\n⏱️ **Auto-Delete Time:** `{del_time} Minutes`\n⏱️ **Token Validity Time:** `{v_expire_hours} Hours`"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Verification: {v_status}", callback_data="adm_toggle_verify"), InlineKeyboardButton(f"Auto Delete: {d_status}", callback_data="adm_toggle_delete")],
        [InlineKeyboardButton(f"Forward Protect: {p_status}", callback_data="adm_toggle_protect"), InlineKeyboardButton("Set Delete Time ⏱️", callback_data="adm_set_time")],
        [InlineKeyboardButton("Set Token Validity 🔑", callback_data="adm_set_token_time"), InlineKeyboardButton("Change Shortener Site & API 🔗", callback_data="adm_change_link")],
        [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard)
