
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, MONGO_URL, LOG_GROUP_ID
from pymongo import MongoClient
from datetime import datetime, timedelta
import asyncio

# MongoDB Connection
client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
reports = db['reports']
active_chats = db['active_chats']
transactions = db['transactions']

def is_owner(func):
    async def wrapper(client, message: Message):
        if message.from_user.id != OWNER_ID:
            return await message.reply("❌ You aren't authorized to use admin commands.")
        return await func(client, message)
    return wrapper

# Stats command
@Client.on_message(filters.command("stats") & filters.private)
@is_owner
async def admin_stats(bot, message: Message):
    total_users = users.count_documents({})
    premium_users = users.count_documents({"premium": True})
    active_chats_count = active_chats.count_documents({})
    pending_reports = reports.count_documents({"status": "pending"})
    
    # Users joined today
    today = str(datetime.now().date())
    users_today = users.count_documents({"joined_at": {"$regex": today}})
    
    # Total coins in circulation
    total_coins = users.aggregate([{"$group": {"_id": None, "total": {"$sum": "$coins"}}}])
    total_coins = list(total_coins)[0]["total"] if list(total_coins) else 0
    
    stats_text = f"""
📊 **Bot Statistics**

👥 **Users**: {total_users}
👑 **Premium Users**: {premium_users}
🆕 **New Today**: {users_today}
💬 **Active Chats**: {active_chats_count}
🚨 **Pending Reports**: {pending_reports}
💰 **Total Coins**: {total_coins}

📈 **Growth Rate**: {((users_today / max(total_users, 1)) * 100):.1f}% today
👑 **Premium Rate**: {((premium_users / max(total_users, 1)) * 100):.1f}%
"""
    
    await message.reply(
        stats_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("🚨 Reports", callback_data="admin_reports")],
            [InlineKeyboardButton("💰 Transactions", callback_data="admin_transactions")],
            [InlineKeyboardButton("📊 Detailed Stats", callback_data="detailed_stats")]
        ])
    )

# Users command
@Client.on_message(filters.command("users") & filters.private)
@is_owner
async def total_users_command(bot, message: Message):
    total = users.count_documents({})
    active_today = users.count_documents({"last_active": {"$regex": str(datetime.now().date())}})
    
    await message.reply(
        f"👥 **User Statistics**\n\n"
        f"📊 Total registered: `{total}`\n"
        f"🟢 Active today: `{active_today}`\n"
        f"📈 Activity rate: {((active_today / max(total, 1)) * 100):.1f}%"
    )

# Broadcast command
@Client.on_message(filters.command("broadcast") & filters.private)
@is_owner
async def broadcast(bot, message: Message):
    if not message.reply_to_message:
        return await message.reply(
            "📩 **Broadcast Message**\n\n"
            "Reply to a message to broadcast it to all users.\n"
            "⚠️ Use this feature responsibly!"
        )

    # Confirmation
    total_users = users.count_documents({})
    confirm_msg = await message.reply(
        f"📢 **Confirm Broadcast**\n\n"
        f"👥 Recipients: {total_users} users\n"
        f"💬 Message: {message.reply_to_message.text[:100]}...\n\n"
        f"Are you sure you want to broadcast this message?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Broadcast", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
        ])
    )

# User search command
@Client.on_message(filters.command("user") & filters.private)
@is_owner
async def user_info(bot, message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply("❌ Usage: /user <user_id>")
        
        user_id = int(parts[1])
        user = users.find_one({"_id": user_id})
        
        if not user:
            return await message.reply("❌ User not found.")
        
        # Get user info from Telegram
        try:
            tg_user = await bot.get_users(user_id)
            username = f"@{tg_user.username}" if tg_user.username else "No username"
        except:
            username = "Unable to fetch"
        
        user_text = f"""
👤 **User Information**

🆔 **ID**: `{user_id}`
📝 **Name**: {user.get('name', 'Not set')}
📱 **Username**: {username}
🎂 **Age**: {user.get('age', 'Not set')}
🚻 **Gender**: {user.get('gender', 'Not set')}
📍 **Location**: {user.get('location', 'Not set')}
💰 **Coins**: {user.get('coins', 0)}
👑 **Premium**: {"Yes" if user.get('premium', False) else "No"}
🎯 **Matches**: {user.get('matches_found', 0)}
💬 **Messages**: {user.get('messages_sent', 0)}
👥 **Referrals**: {user.get('ref_count', 0)}
📅 **Joined**: {user.get('joined_at', 'Unknown')[:10]}
🕒 **Last Active**: {user.get('last_active', 'Unknown')[:10]}
"""
        
        await message.reply(
            user_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Add Coins", callback_data=f"admin_add_coins:{user_id}")],
                [InlineKeyboardButton("👑 Toggle Premium", callback_data=f"admin_toggle_premium:{user_id}")],
                [InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban:{user_id}")],
                [InlineKeyboardButton("📊 User Reports", callback_data=f"admin_user_reports:{user_id}")]
            ])
        )
        
    except ValueError:
        await message.reply("❌ Invalid user ID format.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

# Ban user command
@Client.on_message(filters.command("ban") & filters.private)
@is_owner
async def ban_user(bot, message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply("❌ Usage: /ban <user_id>")
        
        user_id = int(parts[1])
        result = users.update_one({"_id": user_id}, {"$set": {"banned": True, "banned_at": str(datetime.now())}})
        
        if result.modified_count > 0:
            await message.reply(f"✅ User `{user_id}` has been banned.")
            
            # End any active chats
            active_chats.delete_many({"$or": [{"user1": user_id}, {"user2": user_id}]})
            
            # Notify user
            try:
                await bot.send_message(
                    user_id,
                    "🚫 **Account Suspended**\n\n"
                    "Your account has been suspended due to violations of our terms of service.\n"
                    "Contact support if you believe this is a mistake."
                )
            except:
                pass
        else:
            await message.reply("❌ User not found or already banned.")
            
    except ValueError:
        await message.reply("❌ Invalid user ID format.")

# Unban user command
@Client.on_message(filters.command("unban") & filters.private)
@is_owner
async def unban_user(bot, message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply("❌ Usage: /unban <user_id>")
        
        user_id = int(parts[1])
        result = users.update_one({"_id": user_id}, {"$unset": {"banned": "", "banned_at": ""}})
        
        if result.modified_count > 0:
            await message.reply(f"✅ User `{user_id}` has been unbanned.")
            
            # Notify user
            try:
                await bot.send_message(
                    user_id,
                    "✅ **Account Restored**\n\n"
                    "Your account has been restored. Welcome back to FindPartner Bot!\n"
                    "Please follow our community guidelines."
                )
            except:
                pass
        else:
            await message.reply("❌ User not found or not banned.")
            
    except ValueError:
        await message.reply("❌ Invalid user ID format.")

# Reports management
@Client.on_message(filters.command("reports") & filters.private)
@is_owner
async def view_reports(bot, message: Message):
    pending_reports = list(reports.find({"status": "pending"}).limit(10))
    
    if not pending_reports:
        return await message.reply("✅ No pending reports.")
    
    reports_text = "🚨 **Pending Reports**\n\n"
    
    for i, report in enumerate(pending_reports, 1):
        try:
            reporter = await bot.get_users(report["reporter"])
            reported = await bot.get_users(report["reported"])
            
            reports_text += f"{i}. **{report['reason']}**\n"
            reports_text += f"   👤 Reporter: {reporter.first_name} (`{report['reporter']}`)\n"
            reports_text += f"   🎯 Reported: {reported.first_name} (`{report['reported']}`)\n"
            reports_text += f"   📅 Date: {report['timestamp'][:10]}\n\n"
        except:
            reports_text += f"{i}. **{report['reason']}** - Error loading user info\n\n"
    
    await message.reply(reports_text)

# System cleanup command
@Client.on_message(filters.command("cleanup") & filters.private)
@is_owner
async def system_cleanup(bot, message: Message):
    # Clean old inactive chats (older than 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    old_chats = active_chats.count_documents({"started_at": {"$lt": str(cutoff)}})
    
    if old_chats > 0:
        active_chats.delete_many({"started_at": {"$lt": str(cutoff)}})
    
    # Clean old transactions (keep last 30 days)
    cutoff_transactions = datetime.now() - timedelta(days=30)
    old_transactions = transactions.count_documents({"timestamp": {"$lt": str(cutoff_transactions)}})
    
    await message.reply(
        f"🧹 **System Cleanup Complete**\n\n"
        f"🗑️ Removed {old_chats} old chats\n"
        f"📊 Database optimized\n"
        f"✅ System is clean!"
    )
