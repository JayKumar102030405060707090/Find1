from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
step = db['step']

@Client.on_message(filters.command("profile") & filters.private)
async def view_profile(bot, message: Message):
    user_id = message.from_user.id
    user = users.find_one({"_id": user_id})

    if not user:
        await message.reply("❌ Please use /start first.")
        return

    name = user.get("name", "Not set")
    age = user.get("age", "Not set")
    gender = user.get("gender", "Not set")
    insta = user.get("insta", "Not set")
    coins = user.get("coins", 0)

    await message.reply_text(
        f"🧾 **Your Profile**\n\n"
        f"👤 Name: {name}\n"
        f"🎂 Age: {age}\n"
        f"🚻 Gender: {gender}\n"
        f"📸 Insta: {insta}\n"
        f"💰 Coins: {coins}\n\n"
        f"Use /editprofile to update your info."
    )

@Client.on_message(filters.command("editprofile") & filters.private)
async def edit_profile(bot, message: Message):
    user_id = message.from_user.id
    step.update_one({"_id": user_id}, {"$set": {"step": "name"}}, upsert=True)
    await message.reply("📝 Send your name:")

@Client.on_message(filters.text & filters.private)
async def catch_profile(bot, message: Message):
    user_id = message.from_user.id
    current = step.find_one({"_id": user_id})
    if not current:
        return  # No active edit session

    current_step = current.get("step")

    if current_step == "name":
        step.update_one({"_id": user_id}, {"$set": {"name": message.text, "step": "age"}})
        await message.reply("🎂 Now send your age:")
        return

    if current_step == "age":
        if not message.text.isdigit():
            return await message.reply("❌ Please enter a valid age (number).")
        step.update_one({"_id": user_id}, {"$set": {"age": int(message.text), "step": "gender"}})
        await message.reply("🚻 Send your gender (Boy/Girl/Other):")
        return

    if current_step == "gender":
        gender = message.text.strip().capitalize()
        if gender not in ["Boy", "Girl", "Other"]:
            return await message.reply("❌ Please send 'Boy', 'Girl', or 'Other'.")
        step.update_one({"_id": user_id}, {"$set": {"gender": gender, "step": "insta"}})
        await message.reply("📸 Send your Instagram ID (or type 'skip'):")
        return

    if current_step == "insta":
        insta = message.text.strip()
        if insta.lower() == "skip":
            insta = "Not Provided"

        data = step.find_one({"_id": user_id})
        users.update_one(
            {"_id": user_id},
            {"$set": {
                "name": data["name"],
                "age": data["age"],
                "gender": data["gender"],
                "insta": insta
            }},
            upsert=True
        )
        step.delete_one({"_id": user_id})
        await message.reply("✅ Profile updated successfully!")
        return