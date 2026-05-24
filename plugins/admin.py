import asyncio
import re
import pyromod
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
        [InlineKeyboardButton("🔐 VERIFICATION & SWITCH MENU", callback_data="adm_sub_verify")],
        [InlineKeyboardButton("⏱️ AUTO DELETE MENU", callback_data="adm_sub_delete")],
        [InlineKeyboardButton("🎨 START PAGE CUSTOMIZER", callback_data="adm_sub_start_page")],
        [InlineKeyboardButton("👑 PREMIUM USER MENU", callback_data="adm_sub_premium")],
        [InlineKeyboardButton(f"🛡️ PROTECT CONTENT: {p_status}", callback_data="adm_toggle_protect")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_data")]
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
        [InlineKeyboardButton(f"Verification Mode: {v_status}", callback_data="adm_toggle_verify")],
        [InlineKeyboardButton(f"Premium Mode (Lock File): {prem_mode_status}", callback_data="adm_toggle_premium_mode")],
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
# 4. START PAGE SUB-MENU LAYOUT
# -------------------------------------------------------------
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
        [InlineKeyboardButton("✍️ Set Start Text", callback_data="adm_set_start_txt"), 
         InlineKeyboardButton("🗑️ Reset Start Text", callback_data="adm_reset_start_txt")],
        [InlineKeyboardButton("🖼️ Set Start Photo", callback_data="adm_set_start_img"), 
         InlineKeyboardButton("🗑️ Remove Start Photo", callback_data="adm_remove_start_img")],
        [InlineKeyboardButton(f"🎭 Spoiler Mode: {'🟢 ON' if settings.get('start_spoiler', False) else '🔴 OFF'}", callback_data="adm_toggle_spoiler")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="adm_back_main")]
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
        [InlineKeyboardButton("➕ Add Premium ID", callback_data="adm_add_prem"),
         InlineKeyboardButton("🗑️ Remove Premium ID", callback_data="adm_rem_prem")],
        [InlineKeyboardButton("📜 View Premium Users", callback_data="adm_list_prem")],
        [InlineKeyboardButton("🔗 Set Buy Premium Link", callback_data="adm_set_buy_link")],
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
    # --- PREMIUM CONTROL ACTIONS (FIXED PROMPT DELETION) ---
    # =============================================================
    elif action == "add_prem":
        await query.answer() 
        await query.message.delete()
        
        prompt_msg1 = await client.send_message(chat_id, "👑 **[STEP 1/2] Naye Premium User ki UID (Telegram ID) bhejein:**\n\n*(Sirf number baji allow hai. Cancel karne ke liye /cancel likhein)*")
        id_prompt = await client.listen(chat_id, filters=filters.text)
        
        if id_prompt.text.strip() == "/cancel":
            try: await prompt_msg1.delete()
            except: pass
            try: await id_prompt.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        u_input = id_prompt.text.strip()
        if not u_input.isdigit():
            try: await prompt_msg1.delete()
            except: pass
            try: await id_prompt.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_premium")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Kripya sirf numerical Telegram ID send karein.", reply_markup=back_keyboard)
            return

        target_id = int(u_input)
        try: await prompt_msg1.delete()
        except: pass
        
        prompt_msg2 = await client.send_message(chat_id, f"⏱️ **[STEP 2/2] User `{target_id}` ko kitne DINO (Days) ke liye Premium banana hai?**\n\n*(Example: 30 din ke liye '30' likhein. Cancel ke liye /cancel)*")
        days_prompt = await client.listen(chat_id, filters=filters.text)
        
        if days_prompt.text.strip() == "/cancel":
            try: await id_prompt.delete()
            except: pass
            try: await prompt_msg2.delete()
            except: pass
            try: await days_prompt.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        days_input = days_prompt.text.strip()
        if not days_input.isdigit() or int(days_input) <= 0:
            try: await id_prompt.delete()
            except: pass
            try: await prompt_msg2.delete()
            except: pass
            try: await days_prompt.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_premium")]])
            await client.send_message(chat_id, "❌ **Invalid Days!** Kripya sirf positive number bhejiyega (jaise: 1, 7, 30).", reply_markup=back_keyboard)
            return
            
        premium_days = int(days_input)
        expiry_date = await db.add_premium_user(target_id, premium_days)
        formatted_expiry = expiry_date.strftime('%Y-%m-%d %H:%M UTC')
        
        success_msg = await client.send_message(
            chat_id, 
            f"👑 **👑 PREMIUM ACTIVATED SUCCESSFULLY**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User ID:** `{target_id}`\n"
            f"⏱️ **Duration:** `{premium_days} Days`\n"
            f"📅 **Expiry Time:** `{formatted_expiry}`\n\n"
            f"*Yeh user expiry date aate hi automatic list se remove ho jayega.*"
        )
        
        try:
            await client.send_message(
                chat_id=target_id,
                text=(
                    f"🎉 **🎉 CONGRATULATIONS !! 🎉**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Aapke Account par **{premium_days} Dino** ke liye **👑 PREMIUM ACCESS** active kar diya gaya hai!\n\n"
                    f"📅 **Expiry Date:** `{formatted_expiry}`\n\n"
                    f"✨ **Benefits:** Ab aapko bot me koi bhi file download karte waqt **Shortener Ads ya Verification karne ki zarurat nahi padegi**! Aapki saari files seedhe bypass ho jayengi. Enjoy!"
                )
            )
        except Exception as e:
            logger.error(f"Could not send premium activation alert to {target_id}: {e}")
            
        await asyncio.sleep(4)
        try: await success_msg.delete()
        except: pass
        try: await id_prompt.delete()
        except: pass
        try: await prompt_msg2.delete()
        except: pass
        try: await days_prompt.delete()
        except: pass
        
        settings = await db.get_settings()
        text, keyboard = await get_premium_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "rem_prem":
        await query.answer() 
        await query.message.delete()
        
        prompt_msg = await client.send_message(chat_id, "🗑️ **Premium se hatane ke liye User ki UID (Telegram ID) bhejein:**\n\n*(Cancel karne ke liye /cancel likhein)*")
        id_prompt = await client.listen(chat_id, filters=filters.text)
        
        if id_prompt.text.strip() == "/cancel":
            try: await prompt_msg.delete()
            except: pass
            try: await id_prompt.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        u_input = id_prompt.text.strip()
        if not u_input.isdigit():
            try: await prompt_msg.delete()
            except: pass
            try: await id_prompt.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_premium")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Kripya sirf numerical Telegram ID send karein.", reply_markup=back_keyboard)
            return

        target_id = int(u_input)
        is_removed = await db.remove_premium_user(target_id)
        
        if is_removed:
            success_msg = await client.send_message(chat_id, f"🗑️ **User ID** `{target_id}` **Premium List se successfully hata di gayi!**")
            try:
                await client.send_message(
                    chat_id=target_id,
                    text=(
                        f"⚠️ **PREMIUM PLAN EXPIRED / REMOVED**\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"Aapke account se **👑 Premium Access** ko admin dwara remove kar diya gaya hai ya aapka plan expire ho gaya hai.\n\n"
                        f"🔄 Files pane ke liye ab aapko normal users ki tarah verification process complete karna hoga."
                    )
                )
            except Exception as e:
                logger.error(f"Could not send premium removal alert to {target_id}: {e}")
        else:
            success_msg = await client.send_message(chat_id, f"❌ **User ID** `{target_id}` **Premium list mein nahi mila.**")
            
        await asyncio.sleep(3)
        try: await success_msg.delete()
        except: pass
        try: await prompt_msg.delete()
        except: pass
        try: await id_prompt.delete()
        except: pass
        
        settings = await db.get_settings()
        text, keyboard = await get_premium_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "list_prem":
        try: users = await db.get_all_premium_users()
        except Exception: users = []
            
        if not users:
            list_text = "<b>ℹ️ Premium user list bilkul khali hai!</b>"
        else:
            list_text = "📜 **CURRENT PREMIUM USERS LIST**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for idx, u_id in enumerate(users, start=1):
                list_text += f"{idx}. 👤 ID: <code>{u_id}</code>\n"
        
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_sub_premium")]])
        await query.message.edit_text(text=list_text, reply_markup=back_keyboard)
        return

    elif action == "set_buy_link":
        await query.answer()
        await query.message.delete()
        
        prompt_msg = await client.send_message(chat_id, "🔗 **Users ke liye Premium kharidne ka Link bhejein:**\n\n*(Ex: `https://t.me/your_username` ya payment website link. Cancel ke liye /cancel)*")
        link_prompt = await client.listen(chat_id, filters=filters.text)
        
        if link_prompt.text.strip() == "/cancel":
            try: await prompt_msg.delete()
            except: pass
            try: await link_prompt.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_premium_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return
            
        new_link = link_prompt.text.strip()
        await db.update_setting("premium_buy_link", new_link)
        
        success_msg = await client.send_message(chat_id, f"✅ **Premium Buy Link updated successfully!**\n\n`{new_link}`")
        await asyncio.sleep(3)
        try: await success_msg.delete()
        except: pass
        try: await prompt_msg.delete()
        except: pass
        try: await link_prompt.delete()
        except: pass
        
        settings = await db.get_settings()
        text, keyboard = await get_premium_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    # =============================================================
    # --- START PAGE CONTROL ACTIONS (FIXED PROMPT DELETION) ---
    # =============================================================
    elif action == "set_start_txt":
        await query.answer() 
        await query.message.delete()
        
        prompt_msg = await client.send_message(chat_id, "✍️ **Naya /start message text likh kar bhejein:**\n\n*(HTML/Markdown tags use kar sakte hain. Cancel karne ke liye /cancel likhein)*")
        txt_prompt = await client.listen(chat_id, filters=filters.text)
        
        if txt_prompt.text.strip() == "/cancel":
            try: await prompt_msg.delete()
            except: pass
            try: await txt_prompt.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_start_page_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        await db.update_setting("custom_start_text", txt_prompt.text.strip())
        success_msg = await client.send_message(chat_id, "✅ **Start page message text update ho gaya!**")
        await asyncio.sleep(3)
        try: await success_msg.delete()
        except: pass
        try: await prompt_msg.delete()
        except: pass
        try: await txt_prompt.delete()
        except: pass
        
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "reset_start_txt":
        await query.answer() 
        await db.update_setting("custom_start_text", None) 
        await query.answer("Start message default text par reset ho gaya! ⚪", show_alert=True)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    elif action == "set_start_img":
        await query.answer() 
        await query.message.delete()
        
        prompt_msg = await client.send_message(chat_id, "🖼️ **Nayi Start Photo ya image file bhejein (As a Photo):**\n\n*(Cancel karne ke liye /cancel text likh kar send karein)*")
        img_prompt = await client.listen(chat_id)
        
        if img_prompt.text and img_prompt.text.strip() == "/cancel":
            try: await prompt_msg.delete()
            except: pass
            try: await img_prompt.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_start_page_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not img_prompt.photo:
            try: await prompt_msg.delete()
            except: pass
            try: await img_prompt.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_start_page")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Kripya sirf ek image/photo forward ya upload karein.", reply_markup=back_keyboard)
            return
            
        file_id = img_prompt.photo.file_id
        await db.update_setting("start_photo", file_id)
        
        success_msg = await client.send_message(chat_id, "✅ **Start Page Image updated successfully!**")
        await asyncio.sleep(3)
        try: await success_msg.delete()
        except: pass
        try: await prompt_msg.delete()
        except: pass
        try: await img_prompt.delete()
        except: pass
        
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return

    elif action == "remove_start_img":
        await query.answer() 
        await db.update_setting("start_photo", None) 
        await query.answer("Start image successfully remove ho gayi! (Text-Only Mode Enabled) 🗑️", show_alert=True)
        settings = await db.get_settings()
        text, keyboard = await get_start_page_menu_layout(settings)
        await query.message.edit_text(text, reply_markup=keyboard)
        return

    # --- EXISTING VALIDATION CONTROLS (FIXED PROMPT DELETION) ---
    elif action == "set_time":
        await query.answer() 
        await query.message.delete()
        
        prompt_msg = await client.send_message(chat_id, "⏱️ **Auto-Delete ka time minutes me bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*")
        time_msg = await client.listen(chat_id, filters=filters.text)
        
        if time_msg.text.strip() == "/cancel":
            try: await prompt_msg.delete()
            except: pass
            try: await time_msg.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_delete_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        try:
            minutes = int(time_msg.text.strip())
            await db.update_setting("auto_delete_time", minutes * 60)
            success_msg = await client.send_message(chat_id, f"✅ Auto-Delete timer set to **{minutes} Minutes**!")
            await asyncio.sleep(3)
            try: await success_msg.delete()
            except: pass
            try: await prompt_msg.delete()
            except: pass
            try: await time_msg.delete()
            except: pass
            
            settings = await db.get_settings()
            text, keyboard = await get_delete_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
        except ValueError:
            try: await prompt_msg.delete()
            except: pass
            try: await time_msg.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_delete")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Only clean numbers are allowed.", reply_markup=back_keyboard)
        return

    elif action == "set_token_time":
        await query.answer() 
        await query.message.delete()
        
        prompt_msg = await client.send_message(chat_id, "🔑 **Token Validity ka time Hours (Ghante) me bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*")
        time_msg = await client.listen(chat_id, filters=filters.text)
        
        if time_msg.text.strip() == "/cancel":
            try: await prompt_msg.delete()
            except: pass
            try: await time_msg.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        try:
            hours = int(time_msg.text.strip())
            await db.update_setting("verify_expire_time", hours * 3600)
            success_msg = await client.send_message(chat_id, f"✅ Token validity set to **{hours} Hours**!")
            await asyncio.sleep(3)
            try: await success_msg.delete()
            except: pass
            try: await prompt_msg.delete()
            except: pass
            try: await time_msg.delete()
            except: pass
            
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
        except ValueError:
            try: await prompt_msg.delete()
            except: pass
            try: await time_msg.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_verify")]])
            await client.send_message(chat_id, "❌ **Invalid Format!** Only integers/numbers are allowed.", reply_markup=back_keyboard)
        return

    elif action == "change_link":
        await query.message.delete()
        
        prompt_msg1 = await client.send_message(chat_id, "🔗 **Naya Shortener Domain name bhejein:**\n*(Example: `linkshortify.com`)*\n\n*(Process cancel karne ke liye /cancel likhein)*")
        site_msg = await client.listen(chat_id, filters=filters.text)
        new_site = site_msg.text.strip()
        
        if new_site == "/cancel":
            try: await prompt_msg1.delete()
            except: pass
            try: await site_msg.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not is_valid_domain(new_site):
            try: await prompt_msg1.delete()
            except: pass
            try: await site_msg.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_verify")]])
            await client.send_message(chat_id, "❌ **Invalid Domain Format!**\nUse explicit domain formats like `site.com` or `api.cc` without protocols.", reply_markup=back_keyboard)
            return

        try: await prompt_msg1.delete()
        except: pass
        
        prompt_msg2 = await client.send_message(chat_id, "🔑 **Us Website ki API Key bhejein:**\n\n*(Process cancel karne ke liye /cancel likhein)*")
        api_msg = await client.listen(chat_id, filters=filters.text)
        new_api = api_msg.text.strip()
        
        if new_api == "/cancel":
            try: await site_msg.delete()
            except: pass
            try: await prompt_msg2.delete()
            except: pass
            try: await api_msg.delete()
            except: pass
            settings = await db.get_settings()
            text, keyboard = await get_verify_menu_layout(settings)
            await client.send_message(chat_id, text, reply_markup=keyboard)
            return

        if not is_valid_api(new_api):
            try: await site_msg.delete()
            except: pass
            try: await prompt_msg2.delete()
            except: pass
            try: await api_msg.delete()
            except: pass
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="adm_sub_verify")]])
            await client.send_message(chat_id, "❌ **Invalid API Format!**\nAPI strings should contain no spaces and contain valid alphanumeric sequences.", reply_markup=back_keyboard)
            return
        
        await db.update_setting("shortlink_url", new_site)
        await db.update_setting("shortlink_api", new_api)
        
        success_msg = await client.send_message(chat_id, "✅ **Shortener Details Updated Successfully!**")
        await asyncio.sleep(3)
        try: await success_msg.delete()
        except: pass
        try: await site_msg.delete()
        except: pass
        try: await prompt_msg2.delete()
        except: pass
        try: await api_msg.delete()
        except: pass
        
        settings = await db.get_settings()
        text, keyboard = await get_verify_menu_layout(settings)
        await client.send_message(chat_id, text, reply_markup=keyboard)
        return
