
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from pymongo import MongoClient
from datetime import datetime

client = MongoClient(MONGO_URL)
db = client['find_partner']
active_chats = db['active_chats']
reports = db['reports']
blocked_users = db['blocked_users']

@Client.on_message(filters.command("report") & filters.private)
async def report_command(bot, message: Message):
    user_id = message.from_user.id
    chat = active_chats.find_one({"$or": [{"user1": user_id}, {"user2": user_id}]})

    if not chat:
        return await message.reply(
            "❌ **No Active Chat**\n\nYou're not chatting with anyone to report.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Find Match", callback_data="quick_match")]
            ])
        )

    other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]

    if other_user == "AI_BOT":
        return await message.reply(
            "⚠️ **Cannot Report AI**\n\nYou can't report the AI bot. If you're having issues, contact support.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")]
            ])
        )

    await message.reply(
        "🚨 **Report User**\n\nChoose the reason for reporting:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗣️ Abusive Language", callback_data=f"report:abuse:{other_user}")],
            [InlineKeyboardButton("🔞 Inappropriate Content", callback_data=f"report:inappropriate:{other_user}")],
            [InlineKeyboardButton("📱 Spam/Advertising", callback_data=f"report:spam:{other_user}")],
            [InlineKeyboardButton("👤 Fake Profile", callback_data=f"report:fake:{other_user}")],
            [InlineKeyboardButton("💔 Harassment", callback_data=f"report:harassment:{other_user}")],
            [InlineKeyboardButton("🔐 Privacy Violation", callback_data=f"report:privacy:{other_user}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_report")]
        ])
    )

@Client.on_callback_query(filters.regex(r"report:(\w+):(\d+|AI_BOT)"))
async def handle_report(bot, callback: CallbackQuery):
    reason = callback.matches[0].group(1)
    reported_user = callback.matches[0].group(2)
    reporter_id = callback.from_user.id
    
    if reported_user == "AI_BOT":
        return await callback.answer("❌ Cannot report AI bot", show_alert=True)
    
    reported_user = int(reported_user)
    
    # Check if already reported recently
    existing_report = reports.find_one({
        "reporter": reporter_id,
        "reported": reported_user,
        "timestamp": {"$gte": str(datetime.now().date())}  # Today
    })
    
    if existing_report:
        return await callback.answer("⚠️ You've already reported this user today.", show_alert=True)
    
    # Save report
    report_data = {
        "reporter": reporter_id,
        "reported": reported_user,
        "reason": reason,
        "timestamp": str(datetime.now()),
        "status": "pending"
    }
    
    reports.insert_one(report_data)
    
    reason_names = {
        "abuse": "Abusive Language",
        "inappropriate": "Inappropriate Content", 
        "spam": "Spam/Advertising",
        "fake": "Fake Profile",
        "harassment": "Harassment",
        "privacy": "Privacy Violation"
    }
    
    await callback.message.edit_text(
        f"✅ **Report Submitted**\n\n"
        f"🚨 **Reason**: {reason_names.get(reason, reason)}\n"
        f"📅 **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Thank you for reporting. Our team will review this case.\n"
        f"You can also block this user to avoid future contact.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 Block User", callback_data=f"block_user:{reported_user}")],
            [InlineKeyboardButton("🔚 End Chat", callback_data="stop_chat")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )
    
    # Notify admins
    try:
        reporter_info = await bot.get_users(reporter_id)
        reported_info = await bot.get_users(reported_user)
        
        admin_msg = f"""
🚨 **NEW REPORT** 🚨

👤 **Reporter**: {reporter_info.first_name} (`{reporter_id}`)
🎯 **Reported**: {reported_info.first_name} (`{reported_user}`)
📝 **Reason**: {reason_names.get(reason, reason)}
📅 **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

#REPORT #{reason.upper()}
"""
        
        await bot.send_message(LOG_GROUP_ID, admin_msg)
        
    except Exception as e:
        print(f"Error notifying admins: {e}")

@Client.on_callback_query(filters.regex(r"block_user:(\d+)"))
async def block_user(bot, callback: CallbackQuery):
    blocker_id = callback.from_user.id
    blocked_id = int(callback.matches[0].group(1))
    
    # Check if already blocked
    existing_block = blocked_users.find_one({
        "blocker": blocker_id,
        "blocked": blocked_id
    })
    
    if existing_block:
        return await callback.answer("⚠️ User is already blocked.", show_alert=True)
    
    # Block user
    blocked_users.insert_one({
        "blocker": blocker_id,
        "blocked": blocked_id,
        "timestamp": str(datetime.now())
    })
    
    # End current chat if exists
    chat = active_chats.find_one({"$or": [
        {"user1": blocker_id, "user2": blocked_id},
        {"user1": blocked_id, "user2": blocker_id}
    ]})
    
    if chat:
        active_chats.delete_one({"_id": chat["_id"]})
    
    await callback.message.edit_text(
        "🚫 **User Blocked Successfully**\n\n"
        "✅ This user can no longer match with you\n"
        "✅ Any active chat has been ended\n"
        "✅ You won't see them in searches\n\n"
        "You can unblock users anytime from settings.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Manage Blocked Users", callback_data="manage_blocked")],
            [InlineKeyboardButton("🔍 Find New Match", callback_data="quick_match")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("manage_blocked"))
async def manage_blocked_users(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    blocked_list = list(blocked_users.find({"blocker": user_id}))
    
    if not blocked_list:
        await callback.message.edit_text(
            "🚫 **Blocked Users**\n\n✅ You haven't blocked anyone yet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
        )
        return
    
    # Show blocked users
    blocked_text = "🚫 **Blocked Users**\n\n"
    buttons = []
    
    for i, block in enumerate(blocked_list[:10], 1):  # Show first 10
        try:
            blocked_user_info = await bot.get_users(block["blocked"])
            blocked_text += f"{i}. {blocked_user_info.first_name}\n"
            buttons.append([InlineKeyboardButton(
                f"🔓 Unblock {blocked_user_info.first_name}", 
                callback_data=f"unblock:{block['blocked']}"
            )])
        except:
            blocked_text += f"{i}. User {block['blocked']}\n"
            buttons.append([InlineKeyboardButton(
                f"🔓 Unblock User", 
                callback_data=f"unblock:{block['blocked']}"
            )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    
    await callback.message.edit_text(
        blocked_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"unblock:(\d+)"))
async def unblock_user(bot, callback: CallbackQuery):
    blocker_id = callback.from_user.id
    unblock_id = int(callback.matches[0].group(1))
    
    result = blocked_users.delete_one({
        "blocker": blocker_id,
        "blocked": unblock_id
    })
    
    if result.deleted_count > 0:
        try:
            unblocked_user = await bot.get_users(unblock_id)
            name = unblocked_user.first_name
        except:
            name = f"User {unblock_id}"
        
        await callback.answer(f"✅ {name} has been unblocked!", show_alert=True)
        await manage_blocked_users(bot, callback)  # Refresh the list
    else:
        await callback.answer("❌ User was not in your blocked list.", show_alert=True)

@Client.on_callback_query(filters.regex("cancel_report"))
async def cancel_report(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "❌ **Report Cancelled**\n\nNo report was submitted.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Continue Chatting", callback_data="dismiss")],
            [InlineKeyboardButton("🚫 End Chat", callback_data="stop_chat")]
        ])
    )

@Client.on_callback_query(filters.regex("contact_support"))
async def contact_support(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 **Contact Support**\n\n"
        "Need help? Contact our support team:\n\n"
        "📧 Email: support@example.com\n"
        "💬 Telegram: @YourSupportBot\n"
        "🕐 Response time: 24-48 hours",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourUsername")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ])
    )
