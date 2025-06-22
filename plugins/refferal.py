from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']

@Client.on_message(filters.command("refer") & filters.private)
async def refer(bot, message: Message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    await message.reply_text(
        f"🎁 *Refer & Earn!*\n\n"
        f"Invite your friends and earn 5 coins per referral.\n"
        f"Here is your link:\n`{ref_link}`\n\n"
        f"Make sure your friend opens this link and starts the bot.",
        parse_mode="Markdown"
    )

@Client.on_message(filters.command("start") & filters.private)
async def start(bot, message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = None

    if len(args) > 1:
        referred_by = int(args[1]) if args[1].isdigit() else None

    existing_user = users.find_one({"_id": user_id})
    if not existing_user:
        # new user
        users.insert_one({
            "_id": user_id,
            "coins": 5,  # initial bonus
        })
        if referred_by and referred_by != user_id:
            users.update_one({"_id": referred_by}, {"$inc": {"coins": 5}})
            await bot.send_message(
                referred_by,
                f"🎉 You earned 5 coins for referring [this user](tg://user?id={user_id})!",
                parse_mode="Markdown"
            )
        await message.reply("👋 Welcome to *FindPartner Bot!* Use /editprofile to set up your profile.", parse_mode="Markdown")
    else:
        await message.reply("👋 You're already using the bot.")