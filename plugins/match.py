from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from pymongo import MongoClient
from random import choice

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
active_chats = db['active_chats']

waiting_users = {}

def is_chatting(user_id):
    return active_chats.find_one({"$or": [{"user1": user_id}, {"user2": user_id}]})

@Client.on_message(filters.command("find") & filters.private)
async def find_partner(bot, message: Message):
    user_id = message.from_user.id

    if is_chatting(user_id):
        return await message.reply("🔄 You're already in a chat. Use /stop to end it first.")

    for other_id, data in waiting_users.items():
        if other_id != user_id:
            # Match found
            del waiting_users[other_id]
            active_chats.insert_one({"user1": user_id, "user2": other_id, "revealed": False})
            await bot.send_message(other_id, "🎯 Match found! You're now chatting anonymously.\nUse /stop to end.")
            await bot.send_message(user_id, "🎯 Match found! You're now chatting anonymously.\nUse /stop to end.")
            return

    waiting_users[user_id] = {}
    await message.reply("⏳ Looking for a partner... Please wait.")

@Client.on_message(filters.command("stop") & filters.private)
async def stop_chat(bot, message: Message):
    user_id = message.from_user.id
    chat = is_chatting(user_id)

    if chat:
        other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]
        active_chats.delete_one({"_id": chat["_id"]})
        await bot.send_message(other_user, "🚫 The other user has left the chat.")
        await message.reply("✅ You left the chat.")
    else:
        await message.reply("❌ You aren't chatting with anyone currently.")

@Client.on_message(filters.command("reveal") & filters.private)
async def reveal_identity(bot, message: Message):
    user_id = message.from_user.id
    chat = is_chatting(user_id)

    if not chat:
        return await message.reply("❌ You are not in a chat currently.")

    user_data = users.find_one({"_id": user_id})
    if user_data.get("coins", 0) < 100:
        return await message.reply("💸 You need at least 100 coins to send reveal request.")

    other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]

    users.update_one({"_id": user_id}, {"$inc": {"coins": -100}})
    await bot.send_message(
        other_user,
        f"👁️ Someone wants to reveal identity. Spend 100 coins to agree?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Reveal", callback_data=f"reveal_confirm:{user_id}")]
        ])
    )
    await message.reply("🕵️ Reveal request sent. Waiting for their confirmation...")

@Client.on_callback_query(filters.regex(r"reveal_confirm:(\d+)"))
async def confirm_reveal(bot, callback):
    from_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id

    chat = is_chatting(user_id)
    if not chat or (from_id != chat["user1"] and from_id != chat["user2"]):
        return await callback.answer("❌ Chat session expired or invalid.", show_alert=True)

    user_data = users.find_one({"_id": user_id})
    if user_data.get("coins", 0) < 100:
        return await callback.answer("💸 You don't have enough coins.", show_alert=True)

    users.update_one({"_id": user_id}, {"$inc": {"coins": -100}})

    # Reveal both
    from_profile = await bot.get_users(from_id)
    to_profile = await bot.get_users(user_id)

    await bot.send_message(
        from_id,
        f"🎉 Reveal success!\n👤 Their Username: @{to_profile.username or 'Hidden'}\nName: {to_profile.first_name}"
    )
    await bot.send_message(
        user_id,
        f"🎉 Reveal success!\n👤 Their Username: @{from_profile.username or 'Hidden'}\nName: {from_profile.first_name}"
    )

    await callback.answer("✅ Reveal done!")
import asyncio

# Modify existing find_partner function like this:
@Client.on_message(filters.command("find") & filters.private)
async def find_partner(bot, message: Message):
    user_id = message.from_user.id

    if is_chatting(user_id):
        return await message.reply("🔄 You're already in a chat. Use /stop to end it first.")

    # Check for real match first
    for other_id, data in waiting_users.items():
        if other_id != user_id:
            del waiting_users[other_id]
            active_chats.insert_one({"user1": user_id, "user2": other_id, "revealed": False})
            await bot.send_message(other_id, "🎯 Match found! You're now chatting anonymously.\nUse /stop to end.")
            await bot.send_message(user_id, "🎯 Match found! You're now chatting anonymously.\nUse /stop to end.")
            return

    # No match yet, wait a bit
    waiting_users[user_id] = {}
    await message.reply("⏳ Looking for a partner... Please wait 10s.")

    await asyncio.sleep(10)

    # Still no match? Use AI fallback
    if user_id in waiting_users:
        del waiting_users[user_id]
        active_chats.insert_one({"user1": user_id, "user2": "AI_USER", "revealed": False})
        await message.reply("🤖 No real user found. You're now chatting with a bot.\nUse /stop to exit.")

# AI response handler (for "AI_USER" matched sessions)
@Client.on_message(filters.private & filters.text)
async def ai_fallback_reply(bot, message: Message):
    user_id = message.from_user.id
    chat = is_chatting(user_id)

    if not chat:
        return

    partner_id = chat["user1"] if chat["user2"] == user_id else chat["user2"]

    if partner_id == "AI_USER":
        responses = [
            "😊 Hii! How are you?",
            "🤔 What's your favorite movie?",
            "😂 Haha, that's funny!",
            "❤️ Are you single?",
            "💬 Tell me more!",
            "🌍 Where are you from?",
        ]
        await asyncio.sleep(2)
        await message.reply(choice(responses))