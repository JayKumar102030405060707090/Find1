from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID, MONGO_URL  # ✅ FIXED: MONGO_URL imported here
from pymongo import MongoClient
from datetime import datetime

# ✅ MongoDB Connection
client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']

# ✅ Owner check decorator
def is_owner(func):
    async def wrapper(client, message: Message):
        if message.from_user.id != OWNER_ID:
            return await message.reply("❌ You aren't authorized.")
        return await func(client, message)
    return wrapper

# ✅ Command: /users – total registered users
@Client.on_message(filters.command("users") & filters.private)
@is_owner
async def total_users(bot, message: Message):
    total = users.count_documents({})
    await message.reply(f"📊 Total registered users: `{total}`")

# ✅ Command: /broadcast (Reply to a message to broadcast)
@Client.on_message(filters.command("broadcast") & filters.private)
@is_owner
async def broadcast(bot, message: Message):
    if not message.reply_to_message:
        return await message.reply("📩 Reply to a message to broadcast it.")

    sent, failed = 0, 0
    all_users = users.find()

    for user in all_users:
        try:
            await bot.copy_message(
                chat_id=user["_id"],
                from_chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )
            sent += 1
        except:
            failed += 1

    await message.reply(f"📢 Broadcast done.\n✅ Sent: `{sent}`\n❌ Failed: `{failed}`")