import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from plugins.dbusers import db  # Aapka existing database module
from config import *



def make_progress_bar(percentage):
    """Percentage ke hisab se filled aur empty status bar banata hai."""
    filled_length = int(round(10 * percentage / 100))
    # Filled blocks ke liye '█' aur empty ke liye '░' ka use kiya hai
    bar = '█' * filled_length + '░' * (10 - filled_length)
    return bar

@Client.on_message(filters.command("plan") & filters.private)
async def plan_command_handler(client: Client, message: Message):
    premium_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Qʀ Code", callback_data="show_premium_qr"),
            InlineKeyboardButton("💳 Uᴘɪ ID", callback_data="show_premium_upi")
        ],
        [InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close_data")]
    ])
    await message.reply_text(text=PREMIUM_PLANS_TEXT, reply_markup=premium_keyboard)


@Client.on_message(filters.command("myplan") & filters.private)
async def my_plan_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    
    is_premium = await db.check_premium_status(user_id) if hasattr(db, 'check_premium_status') else False

    if is_premium:
        # DB se timestamps nikalne ka logic (Placeholders - inhe apne DB functions se badlein)
        # Maan lete hain ki aapke DB me integers/timestamps save hote hain
        current_time = int(time.time())
        
        # Default fallback values (agar aapke DB me expiry track nahi ho rahi toh lifetime active dikhayega)
        start_time = current_time
        expiry_time = current_time + 1  # Safe fallback
        
        if hasattr(db, 'get_premium_start_time'): # Kab shuru hua
            start_time = await db.get_premium_start_time(user_id) or current_time
        if hasattr(db, 'get_premium_expiry_time'): # Kab expire hoga
            expiry_time = await db.get_premium_expiry_time(user_id) or (current_time + 86400)

        total_duration = expiry_time - start_time
        time_passed = current_time - start_time
        
        # Percentage calculation for status bar
        if total_duration > 0:
            percentage = (time_passed / total_duration) * 100
            percentage = max(0, min(100, percentage)) # 0% se 100% ke beech bound rakhne ke liye
            # Hame filled bar bache hue din ke liye chahiye, isliye inverse percent nikalenge
            remaining_percentage = 100 - percentage
        else:
            remaining_percentage = 100

        # Visual Bar Generator
        status_bar = make_progress_bar(remaining_percentage)
        
        # Remaining time text calculation
        remaining_seconds = expiry_time - current_time
        if remaining_seconds > 0:
            rem_days = remaining_seconds // 86400
            rem_hours = (remaining_seconds % 86400) // 3600
            validity_text = f"⏳ <b>{rem_days} Days, {rem_hours} Hours remaining</b>"
        else:
            validity_text = "⚠️ <b>Expiring soon / Expired</b>"
            status_bar = make_progress_bar(0)
            remaining_percentage = 0

        # Date formatting for User Display
        expiry_date_str = datetime.fromtimestamp(expiry_time).strftime('%d-%m-%Y %H:%M')

        success_text = (
            "👑 <b>YOUR PREMIUM STATUS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user_mention}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            "✨ <b>Status:</b> Premium User (Active)\n"
            f"📅 <b>Expiry:</b> {expiry_date_str}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Usage Limit/Time:</b>\n"
            f"|{status_bar}| {int(remaining_percentage)}%\n\n"
            f"{validity_text}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 No ads, no limits! Direct files are active."
        )
        await message.reply_text(text=success_text)
        
    else:
        # Non-premium (Free) User UI with Empty Bar
        empty_bar = make_progress_bar(0) # 0% visual status
        free_text = (
            "⚠️ <b>YOUR PREMIUM STATUS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user_mention}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            "✨ <b>Status:</b> Free User (No Active Plan)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Premium Bar:</b>\n"
            f"|{empty_bar}| 0%\n\n"
            "❌ Aap free plan par hain. Har file download karne ke liye aapko links bypass ya verify karna hoga.\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Premium access chahiye? Niche diye button par click karein."
        )
        
        buy_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Buy Premium ⭐", callback_data="buy_premium_panel")],
            [InlineKeyboardButton("❌ Close", callback_data="close_data")]
        ])
        await message.reply_text(text=free_text, reply_markup=buy_keyboard)
