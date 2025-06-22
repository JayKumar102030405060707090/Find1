from pyrogram import Client, filters
from config import *
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pyrogram.types import Message
from datetime import datetime

# Logger Setup
logging.basicConfig(level=logging.INFO)
LOGS = logging.getLogger("FindPartnerBot")

# MongoDB Setup with error check
try:
    mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    mongo.server_info()  # Force connection check
    db = mongo["find_partner"]
    users = db["users"]
    LOGS.info("✅ MongoDB connected successfully.")
except ConnectionFailure as e:
    LOGS.error(f"❌ MongoDB connection failed: {e}")
    exit()

# Pyrogram Bot Setup
bot = Client(
    "FindPartnerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

# /start command
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or "None"

    user = users.find_one({"_id": user_id})

    if not user:
        users.insert_one({
            "_id": user_id,
            "name": first_name,
            "username": username,
            "coins": 0,
            "gender": None,
            "age": None,
            "ref_by": None,
            "ref_count": 0,
            "verified": False,
            "joined_at": str(datetime.now())
        })

        # Referral handling
        if len(message.command) > 1:
            try:
                referrer_id = int(message.command[1])
                if referrer_id != user_id:
                    ref_user = users.find_one({"_id": referrer_id})
                    if ref_user:
                        users.update_one({"_id": referrer_id}, {"$inc": {"coins": REFERRAL_COIN, "ref_count": 1}})
                        users.update_one({"_id": user_id}, {"$set": {"ref_by": referrer_id}})
                        await client.send_message(
                            referrer_id,
                            f"🎉 You earned {REFERRAL_COIN} coins for referring {first_name}!"
                        )
            except Exception as e:
                LOGS.warning(f"Referral error: {e}")

    # Welcome message
    await message.reply_text(
        f"👋 Hello {first_name}!\n\n"
        "Welcome to *FindPartner Bot* 💞\n\n"
        "🎯 Use /profile to set your profile.\n"
        "🔍 Use /find to meet someone anonymously.\n"
        "💰 Use /wallet to check your coins.",
        quote=True
    )

    # Send to log group
    try:
        await client.send_message(
            LOG_GROUP_ID,
            f"#NEW_USER\nID: `{user_id}`\nName: [{first_name}](tg://user?id={user_id})"
        )
    except Exception as e:
        LOGS.warning(f"Log group error: {e}")

# Load admin commands if available
try:
    from admin import commands
except Exception as e:
    LOGS.warning(f"Admin module not loaded: {e}")

# Start the bot
if __name__ == "__main__":
    LOGS.info("✅ Bot is starting...")
    bot.run()