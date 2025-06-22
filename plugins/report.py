from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from pymongo import MongoClient
from datetime import datetime

client = MongoClient(MONGO_URL)
db = client['find_partner']
active_chats = db['active_chats']

@Client.on_message(filters.command("report") & filters.private)
async def report_user(bot, message: Message):
    user_id = message.from_user.id
    chat = active_chats.find_one({"$or": [{"user1": user_id}, {"user2": user_id}]})

    if not chat:
        return await message.reply("❌ You're not chatting with anyone to report.")

    other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]

    if other_user == "AI_USER":
        return await message.reply("⚠️ You can't report the AI bot.")

    await message.reply(
        "🚨 Choose the reason to report your chat partner:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗣️ Abuse", callback_data=f"rep:abuse:{user_id}:{other_user}")],
            [InlineKeyboardButton("👎 Bad Behavior", callback_data=f"rep:bad:{user_id}:{other_user}")],
            [InlineKeyboardButton("🔞 Inappropriate", callback_data=f"rep:adult:{user_id}:{other_user}")],
        ])
    )

@Client.on_callback_query(filters.regex(r"rep:(\w+):(\d+):(\d+)"))
async def handle_report_callback(bot, callback):
    reason, from_id, to_id = callback.matches[0].groups()
    from_id, to_id = int(from_id), int(to_id)

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_msg = (
        f"🚨 *User Reported!*\n\n"
        f"*From:* `{from_id}`\n"
        f"*Against:* `{to_id}`\n"
        f"*Reason:* `{reason}`\n"
        f"*Time:* `{time}`\n\n"
        f"_Please review and take action manually._"
    )

    await bot.send_message(LOG_GROUP_ID, report_msg)
    await callback.message.edit("✅ Report submitted. Thank you for helping keep this platform safe.")
    await callback.answer("Report sent!", show_alert=True)