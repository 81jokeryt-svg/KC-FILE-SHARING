import asyncio
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from plugins.dbusers import *
from utils import *

logger = logging.getLogger(__name__)

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
# LAYOUT GENERATORS
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

async def get_start_page_menu_layout(settings):
    has_photo = "🟢 Set (Custom)" if settings.get("start_photo") else "🔴 Not Set (Text Only)"
    has_text = "🟢 Custom Text Enabled" if settings.get("custom_start_text") else "⚪ Default Text Enabled"
    s_status = "🟢 ON (Blurred Image)" if settings.get("start_spoiler", False) else "🔴 OFF (Clear Image)"
    text = (
        "🎨 **START PAGE CONFIGURATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ **Start Photo Status:** `{has_photo}`\n"
        f"📝 **Start Text Status:** `{has_text}`\n"
        f"⚠️ **Spoiler Status:** `{s_status}`\n\n"
        "Aap niche diye gaye button se live /start command ke message, photo aur spoiler toggle badal sakte hain."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ 𝗦𝗘𝗧 𝗦𝗧𝗔𝗥𝗧 𝗧𝗘𝗫𝗧", callback_data="adm_set_start_txt")], 
        [InlineKeyboardButton("🗑️ 𝗥𝗘𝗦𝗘𝗧 𝗦𝗧𝗔𝗥𝗧 𝗧𝗘𝗫𝗧", callback_data="adm_reset_start_txt")],
        [InlineKeyboardButton("🖼️ 𝗦𝗘𝗧 𝗦𝗧𝗔𝗥𝗧 𝗣𝗛𝗢𝗧𝗢", callback_data="adm_set_start_img")], 
        [InlineKeyboardButton("🗑️ 𝗥𝗘𝗠𝗢𝗩𝗘 𝗦𝗧𝗔𝗥𝗧 𝗣𝗛𝗢𝗧𝗢", callback_data="adm_remove_start_img")],
        [InlineKeyboardButton(f"🎭 𝗦🇵🇴🇮🇱🇪🇷 𝗠𝗢𝗗𝗘: {'🟢 ON' if settings.get('start_spoiler', False) else '🔴 OFF'}", callback_data="adm_toggle_spoiler")],
        [InlineKeyboardButton("𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨", callback_data="adm_back_main")]
    ])
    return text, keyboard

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


# --- COMMAND HANDLERS ---
@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("open_admin_from_start"))
async def open_admin_from_start(client, query):
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return
    settings = await db.get_settings()
    text, keyboard = await get_main_panel_layout(settings)
    keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
    await query.message.edit_text(text, reply_markup=keyboard)


# --- CENTRAL CALLBACK ROUTER ---
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

    # --- TOGGLES ACTIONS ---
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
        if "🔙 Back to Home" in str(query.message.reply_markup):
            keyboard.inline_keyboard[-1] = [InlineKeyboardButton("🔙 Back to Home", callback_data="start")]
        await query.message.edit_text(text, reply_markup=keyboard)

    elif action == "toggle_spoiler":
        new_val = not settings.get("start_spoiler", False)
        await db.update_setting("start_spoiler", new_val)
        await query.answer(f"Spoiler Mode {'Enabled 🟢' if new_val else 'Disabled 🔴'}")
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    # =============================================================
    # 👑 ADD PREMIUM USER (WITH FIXED & CUSTOM OPTIONS)
    # =============================================================
    elif action == "add_prem":
        await query.answer()
        await query.message.edit_text(
            text="👤 **NOW SEND ME USER ID**\n\n`/cancel` - Cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]])
        )
        
        id_prompt = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await id_prompt.delete()

        if id_prompt.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return

        u_input = id_prompt.text.strip()
        if not u_input.isdigit():
            await query.message.edit_text("❌ **Invalid Format!** Numerical ID bhejiye.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]]))
            return

        target_id = int(u_input)
        
        validity_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 3 Days", callback_data=f"setup_plan_3_{target_id}")],
            [InlineKeyboardButton("📅 1 Week", callback_data=f"setup_plan_7_{target_id}")],
            [InlineKeyboardButton("📅 1 Month", callback_data=f"setup_plan_30_{target_id}")],
            [InlineKeyboardButton("✍️ Custom Days", callback_data=f"setup_custom_days_{target_id}")],
            [InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]
        ])
        
        await query.message.edit_text(
            text=f"**CHOOSE YOUR PLAN VALIDITY FOR THIS USER:** `{target_id}`",
            reply_markup=validity_keyboard
        )
        return

    # =============================================================
    # 🗑️ REMOVE PREMIUM USER
    # =============================================================
    elif action == "rem_prem":
        await query.answer()
        await query.message.edit_text(
            text="🗑️ **NOW SEND ME USER ID TO REMOVE**\n\n`/cancel` - Cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]])
        )
        
        id_prompt = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await id_prompt.delete()

        if id_prompt.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return

        u_input = id_prompt.text.strip()
        if not u_input.isdigit():
            await query.message.edit_text("❌ **Invalid ID!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]]))
            return

        target_id = int(u_input)
        is_removed = await db.remove_premium_user(target_id)
        
        status_txt = f"🗑️ **Premium access removed for ID:** `{target_id}`" if is_removed else f"❌ **ID** `{target_id}` **not found in Premium list.**"
        
        if is_removed:
            try: await client.send_message(chat_id=target_id, text="⚠️ **PREMIUM PLAN EXPIRED / REMOVED**\n━━━━━━━━━━━━━━━━━━━━\nAapka premium plan end ho chuka hai.")
            except Exception: pass

        await query.message.edit_text(status_txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]]))
        return

    elif action == "list_prem":
        try: users = await db.get_all_premium_users()
        except Exception: users = []
        if not users:
            list_text = "<b>ℹ️ Premium user list khali hai!</b>"
        else:
            list_text = "📜 **CURRENT PREMIUM USERS LIST**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for idx, u_id in enumerate(users, start=1):
                list_text += f"{idx}. 👤 ID: <code>{u_id}</code>\n"
        await query.message.edit_text(text=list_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_sub_premium")]]))
        return

    # =============================================================
    # 🔘 SET PREMIUM BUY LINK
    # =============================================================
    elif action == "set_buy_link":
        await query.answer()
        await query.message.edit_text("🔗 **SEND NEW PREMIUM BUY LINK:**\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]]))
        
        link_prompt = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await link_prompt.delete()
        
        if link_prompt.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        await db.update_setting("premium_buy_link", link_prompt.text.strip())
        await query.message.edit_text("✅ **Buy Link Updated Successfully!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]]))
        return

    # =============================================================
    # ✍️ SET START PAGE TEXT
    # =============================================================
    elif action == "set_start_txt":
        await query.answer()
        await query.message.edit_text("✍️ **SEND NEW /START TEXT:**\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_start_page")]]))
        
        txt_prompt = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await txt_prompt.delete()
        
        if txt_prompt.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_start_page_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        await db.update_setting("custom_start_text", txt_prompt.text.strip())
        await query.message.edit_text("✅ **Start Text Updated Successfully!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_start_page")]]))
        return

    elif action == "reset_start_txt":
        await query.answer()
        await db.update_setting("custom_start_text", None)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    # =============================================================
    # 🖼️ SET START PHOTO
    # =============================================================
    elif action == "set_start_img":
        await query.answer()
        await query.message.edit_text("🖼️ **UPLOAD/FORWARD NEW PHOTO NOW:**\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_start_page")]]))
        
        img_prompt = await client.ask(chat_id, user_id=query.from_user.id)
        await img_prompt.delete()
        
        if img_prompt.text and img_prompt.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_start_page_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        if not img_prompt.photo:
            await query.message.edit_text("❌ **Invalid Format!** Kripya image hi bhejein.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_start_page")]]))
            return
            
        await db.update_setting("start_photo", img_prompt.photo.file_id)
        await query.message.edit_text("✅ **Start Image Configured!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_start_page")]]))
        return

    elif action == "remove_start_img":
        await query.answer()
        await db.update_setting("start_photo", None)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    # =============================================================
    # ⏱️ SET AUTO DELETE TIMER
    # =============================================================
    elif action == "set_time":
        await query.answer()
        await query.message.edit_text("⏱️ **SEND DELETE TIMER MINUTES:**\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_delete")]]))
        
        time_msg = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await time_msg.delete()
        
        if time_msg.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_delete_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        try:
            minutes = int(time_msg.text.strip())
            await db.update_setting("auto_delete_time", minutes * 60)
            await query.message.edit_text(f"✅ **Timer configured to {minutes} Minutes!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_delete")]]))
        except ValueError:
            await query.message.edit_text("❌ **Format Error!** Sirf number allow hai.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_delete")]]))
        return

    # =============================================================
    # 🔑 SET TOKEN VALIDITY HOURS
    # =============================================================
    elif action == "set_token_time":
        await query.answer()
        await query.message.edit_text("🔑 **SEND TOKEN VALIDITY HOURS:**\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
        
        time_msg = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await time_msg.delete()
        
        if time_msg.text.strip() == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        try:
            hours = int(time_msg.text.strip())
            await db.update_setting("verify_expire_time", hours * 3600)
            await query.message.edit_text(f"✅ **Validity set to {hours} Hours!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
        except ValueError:
            await query.message.edit_text("❌ **Format Error!** Sirf number allow hai.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
        return

    # =============================================================
    # 🔗 CHANGE SHORTENER DOMAIN & API STRING
    # =============================================================
    elif action == "change_link":
        await query.answer()
        await query.message.edit_text("🔗 **SEND NEW SHORTENER DOMAIN:**\n*(Ex: linkshortify.com)*\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
        
        site_msg = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await site_msg.delete()
        new_site = site_msg.text.strip()
        
        if new_site == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        if not is_valid_domain(new_site):
            await query.message.edit_text("❌ **Invalid Domain layout.** Protocol bina daale bhejein (eg. `site.com`).", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
            return

        await query.message.edit_text("🔑 **NOW SEND API KEY FOR THE WEBSITE:**\n\n`/cancel` to abort.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
        
        api_msg = await client.ask(chat_id, user_id=query.from_user.id, filters=filters.text)
        await api_msg.delete()
        new_api = api_msg.text.strip()
        
        if new_api == "/cancel":
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await query.message.edit_text(text, reply_markup=keyboard)
            return
            
        if not is_valid_api(new_api):
            await query.message.edit_text("❌ **Invalid API Credentials string.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
            return
        
        await db.update_setting("shortlink_url", new_site)
        await db.update_setting("shortlink_api", new_api)
        await query.message.edit_text("✅ **Shortener Link Properties Updated!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_verify")]]))
        return


# =============================================================
# ✍️ ROUTER FOR STEP 2.5: ASKING CUSTOM DAYS VALUE SMOOTHLY
# =============================================================
@Client.on_callback_query(filters.regex(r"^setup_custom_days_"))
async def ask_custom_days_value(client, callback_query):
    await callback_query.answer()
    target_id = int(callback_query.data.split("_")[3])
    chat_id = callback_query.message.chat.id

    await callback_query.message.edit_text(
        text=f"⏱️ **[CUSTOM PLAN] User `{target_id}` ko kitne DINO (Days) ke liye Premium banana hai?**\n\n*(Example: 45 din ke liye '45' likhein. Cancel ke liye `/cancel`)*",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 CANCEL", callback_data="adm_sub_premium")]])
    )

    days_prompt = await client.ask(chat_id, user_id=callback_query.from_user.id, filters=filters.text)
    await days_prompt.delete()

    if days_prompt.text.strip() == "/cancel":
        settings = await db.get_settings()
        text, keyboard = await get_premium_menu_layout(settings)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        return

    days_input = days_prompt.text.strip()
    if not days_input.isdigit() or int(days_input) <= 0:
        await callback_query.message.edit_text(
            text="❌ **Invalid Days!** Kripya sirf positive number bhejiyega (jaise: 15, 45, 90).", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]])
        )
        return

    custom_premium_days = int(days_input)
    expiry_date = await db.add_premium_user(target_id, custom_premium_days)
    formatted_expiry = expiry_date.strftime('%Y-%m-%d %H:%M UTC')

    success_text = (
        f"✅ **Premium access added to the user with id - {target_id}.**\n\n"
        f"📅 **Custom Duration:** `{custom_premium_days} Days`\n"
        f"⏳ **Expires On:** `{formatted_expiry}`"
    )
    
    try:
        await client.send_message(
            chat_id=target_id,
            text=f"🎉 **CONGRATULATIONS !!** 🎉\n━━━━━━━━━━━━━━━━━━━━\nAapke Account par **{custom_premium_days} Dino** ke liye **👑 PREMIUM ACCESS** active ho gaya hai!"
        )
    except Exception: pass

    await callback_query.message.edit_text(
        text=success_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]])
    )


# -------------------------------------------------------------
# 🚀 ROUTER FOR STATIC PLAN VALIDITY BUTTONS SELECTION (3, 7, 30 Days)
# -------------------------------------------------------------
@Client.on_callback_query(filters.regex(r"^setup_plan_"))
async def process_dynamic_plan_save(client, callback_query):
    data_parts = callback_query.data.split("_")
    premium_days = int(data_parts[2])
    target_id = int(data_parts[3])

    expiry_date = await db.add_premium_user(target_id, premium_days)
    formatted_expiry = expiry_date.strftime('%Y-%m-%d %H:%M UTC')

    success_text = (
        f"✅ **Premium access added to the user with id - {target_id}.**\n\n"
        f"📅 **Plan Duration:** `{premium_days} Days`\n"
        f"⏳ **Expires On:** `{formatted_expiry}`"
    )
    
    try:
        await client.send_message(
            chat_id=target_id,
            text=f"🎉 **CONGRATULATIONS !!** 🎉\n━━━━━━━━━━━━━━━━━━━━\nAapke Account par **{premium_days} Dino** ke liye **👑 PREMIUM ACCESS** active ho gaya hai!"
        )
    except Exception: pass

    await callback_query.message.edit_text(
        text=success_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="adm_sub_premium")]])
    )
