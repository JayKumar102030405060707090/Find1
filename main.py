
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import asyncio
import os
from threading import Thread
from flask import Flask, jsonify

# Logger Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGS = logging.getLogger("FindPartnerBot")

# MongoDB Setup with error check
try:
    mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    mongo.server_info()
    db = mongo["find_partner"]
    users = db["users"]
    LOGS.info("✅ ᴍᴏɴɢᴏᴅʙ ᴄᴏɴɴᴇᴄᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")
except ConnectionFailure as e:
    LOGS.error(f"❌ ᴍᴏɴɢᴏᴅʙ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ғᴀɪʟᴇᴅ: {e}")
    exit()

# Pyrogram Bot Setup
bot = Client(
    "FindPartnerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

def tiny_caps(text):
    """Convert text to tiny caps font"""
    tiny_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ',
        'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
        'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
        'y': 'ʏ', 'z': 'ᴢ', 'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ',
        'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ',
        'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return ''.join(tiny_map.get(char, char) for char in text)

def get_main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 ᴘʀᴏғɪʟᴇ", callback_data="menu_profile"),
            InlineKeyboardButton("🔍 ғɪɴᴅ ᴘᴀʀᴛɴᴇʀ", callback_data="menu_find")
        ],
        [
            InlineKeyboardButton("💰 ᴡᴀʟʟᴇᴛ", callback_data="menu_wallet"),
            InlineKeyboardButton("🎁 ʀᴇғᴇʀʀᴀʟ", callback_data="menu_referral")
        ],
        [
            InlineKeyboardButton("⚙️ sᴇᴛᴛɪɴɢs", callback_data="menu_settings"),
            InlineKeyboardButton("📊 sᴛᴀᴛs", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton("🆘 ʜᴇʟᴘ", callback_data="menu_help"),
            InlineKeyboardButton("📞 sᴜᴘᴘᴏʀᴛ", callback_data="menu_support")
        ]
    ])

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
            "coins": DAILY_BONUS,
            "gender": None,
            "age": None,
            "location": None,
            "bio": None,
            "interests": [],
            "looking_for": None,
            "ref_by": None,
            "ref_count": 0,
            "premium": False,
            "verified": False,
            "matches_found": 0,
            "messages_sent": 0,
            "last_active": str(datetime.now()),
            "joined_at": str(datetime.now()),
            "daily_bonus_claimed": str(datetime.now().date())
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
                        try:
                            await client.send_message(
                                referrer_id,
                                tiny_caps(f"🎉 You earned {REFERRAL_COIN} coins for referring {first_name}!\n💰 Keep sharing your referral link to earn more!")
                            )
                        except:
                            pass
            except Exception as e:
                LOGS.warning(f"Referral error: {e}")

    # Update last active
    users.update_one({"_id": user_id}, {"$set": {"last_active": str(datetime.now())}})

    # Welcome message with main menu
    welcome_text = tiny_caps(f"""
🌟 **Welcome to FindPartner Bot** 🌟

Hello {first_name}! 👋

I'm your personal matchmaking assistant. Here's what I can help you with:

🔍 **Find Partners** - Meet new people anonymously
👤 **Profile Setup** - Create an attractive profile
💰 **Earn Coins** - Get coins through referrals and daily bonuses
🎁 **Premium Features** - Unlock advanced matching features
📊 **Statistics** - Track your interactions and matches

Use the buttons below to get started! ⬇️
""")

    await message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(),
        quote=True
    )

    # Send to log group (with error handling)
    try:
        if LOG_GROUP_ID:
            await client.send_message(
                LOG_GROUP_ID,
                tiny_caps(f"#NEW_USER\nID: `{user_id}`\nName: [{first_name}](tg://user?id={user_id})\nJoined: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            )
    except Exception as e:
        LOGS.warning(f"Log group error: {e}")

@bot.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Main menu callbacks
        if data == "main_menu" or data == "back_menu":
            await callback_query.message.edit_text(
                tiny_caps("🌟 **ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ!** 🌟\n\nᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴅᴏ ᴛᴏᴅᴀʏ?"),
                reply_markup=get_main_menu()
            )
        
        elif data == "menu_profile":
            await callback_query.message.edit_text(
                tiny_caps("👤 **ᴘʀᴏғɪʟᴇ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ**\n\nᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ ᴛᴏ ɢᴇᴛ ʙᴇᴛᴛᴇʀ ᴍᴀᴛᴄʜᴇs:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴘʀᴏғɪʟᴇ", callback_data="edit_profile")],
                    [InlineKeyboardButton("👀 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="view_profile")],
                    [InlineKeyboardButton("🎯 ᴍᴀᴛᴄʜɪɴɢ ᴘʀᴇғᴇʀᴇɴᴄᴇs", callback_data="match_preferences")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_find":
            await callback_query.message.edit_text(
                tiny_caps("🔍 **ғɪɴᴅ ʏᴏᴜʀ ᴍᴀᴛᴄʜ**\n\nᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴍᴀᴛᴄʜɪɴɢ ᴘʀᴇғᴇʀᴇɴᴄᴇ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 ǫᴜɪᴄᴋ ᴍᴀᴛᴄʜ", callback_data="quick_match")],
                    [InlineKeyboardButton("🔧 ɢᴇɴᴅᴇʀ ғɪʟᴛᴇʀ", callback_data="gender_filter")],
                    [InlineKeyboardButton("📍 ʟᴏᴄᴀᴛɪᴏɴ ғɪʟᴛᴇʀ", callback_data="location_filter")],
                    [InlineKeyboardButton("🤖 ᴄʜᴀᴛ ᴡɪᴛʜ ᴀɪ ʙᴏᴛ", callback_data="ai_match")],
                    [InlineKeyboardButton("💕 ғʟɪʀᴛ ᴍᴏᴅᴇ", callback_data="flirt_mode")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_wallet":
            user_data = users.find_one({"_id": user_id})
            coins = user_data.get("coins", 0) if user_data else 0
            premium = user_data.get("premium", False) if user_data else False
            
            wallet_text = tiny_caps(f"""💰 **ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ**

💎 **ʙᴀʟᴀɴᴄᴇ**: {coins} ᴄᴏɪɴs
👑 **sᴛᴀᴛᴜs**: {"ᴘʀᴇᴍɪᴜᴍ ✨" if premium else "ғʀᴇᴇ ᴜsᴇʀ"}

**💸 ᴄᴏɪɴ ᴘʀɪᴄᴇs:**
• 100 ᴄᴏɪɴs = ₹20
• 500 ᴄᴏɪɴs = ₹80 (20% ᴏғғ!)
• 1000 ᴄᴏɪɴs = ₹150 (25% ᴏғғ!)

**🎯 ғᴇᴀᴛᴜʀᴇs ᴄᴏsᴛ:**
• ʀᴇᴠᴇᴀʟ ɪᴅᴇɴᴛɪᴛʏ: 100 ᴄᴏɪɴs
• ᴘʀᴇᴍɪᴜᴍ ᴜᴘɢʀᴀᴅᴇ: 500 ᴄᴏɪɴs
• ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ: 30 ᴄᴏɪɴs ᴘᴇʀ ᴜsᴇ""")
            
            await callback_query.message.edit_text(
                wallet_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁 ᴅᴀɪʟʏ ʙᴏɴᴜs", callback_data="daily_bonus")],
                    [InlineKeyboardButton("💳 ʙᴜʏ ᴄᴏɪɴs", callback_data="buy_coins")],
                    [InlineKeyboardButton("🔑 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_menu")],
                    [InlineKeyboardButton("👑 ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ", callback_data="get_premium")],
                    [InlineKeyboardButton("📊 ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ʜɪsᴛᴏʀʏ", callback_data="transaction_history")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_referral":
            user_data = users.find_one({"_id": user_id})
            ref_count = user_data.get("ref_count", 0) if user_data else 0
            total_earned = ref_count * REFERRAL_COIN
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            
            referral_text = tiny_caps(f"""🎁 **ʀᴇғᴇʀʀᴀʟ ᴘʀᴏɢʀᴀᴍ** 🎁

💰 **ᴇᴀʀɴ {REFERRAL_COIN} ᴄᴏɪɴs** ғᴏʀ ᴇᴀᴄʜ ғʀɪᴇɴᴅ ʏᴏᴜ ʀᴇғᴇʀ!

📊 **ʏᴏᴜʀ sᴛᴀᴛs:**
👥 **ᴛᴏᴛᴀʟ ʀᴇғᴇʀʀᴀʟs**: {ref_count}
💎 **ᴄᴏɪɴs ᴇᴀʀɴᴇᴅ**: {total_earned}

🔗 **ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ:**
`{ref_link}`

**ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:**
1️⃣ sʜᴀʀᴇ ʏᴏᴜʀ ʟɪɴᴋ ᴡɪᴛʜ ғʀɪᴇɴᴅs
2️⃣ ᴛʜᴇʏ ᴊᴏɪɴ ᴜsɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ
3️⃣ ʏᴏᴜ ʙᴏᴛʜ ɢᴇᴛ {REFERRAL_COIN} ᴄᴏɪɴs ɪɴsᴛᴀɴᴛʟʏ!""")
            
            await callback_query.message.edit_text(
                referral_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 sʜᴀʀᴇ ʟɪɴᴋ", switch_inline_query=f"ᴊᴏɪɴ ғɪɴᴅᴘᴀʀᴛɴᴇʀ ʙᴏᴛ ᴀɴᴅ ɢᴇᴛ ғʀᴇᴇ ᴄᴏɪɴs! {ref_link}")],
                    [InlineKeyboardButton("📋 ᴄᴏᴘʏ ʟɪɴᴋ", callback_data=f"copy_link:{user_id}")],
                    [InlineKeyboardButton("👥 ᴍʏ ʀᴇғᴇʀʀᴀʟs", callback_data="my_referrals")],
                    [InlineKeyboardButton("🎯 ʀᴇғᴇʀʀᴀʟ ʀᴇᴡᴀʀᴅs", callback_data="ref_rewards")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_settings":
            await callback_query.message.edit_text(
                tiny_caps("⚙️ **sᴇᴛᴛɪɴɢs**\n\nᴄᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ ᴇxᴘᴇʀɪᴇɴᴄᴇ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs", callback_data="notification_settings")],
                    [InlineKeyboardButton("🔒 ᴘʀɪᴠᴀᴄʏ", callback_data="privacy_settings")],
                    [InlineKeyboardButton("🚫 ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs", callback_data="manage_blocked_users")],
                    [InlineKeyboardButton("🌐 ʟᴀɴɢᴜᴀɢᴇ", callback_data="language_settings")],
                    [InlineKeyboardButton("🎨 ᴛʜᴇᴍᴇ", callback_data="theme_settings")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_stats":
            user_data = users.find_one({"_id": user_id})
            
            if user_data:
                stats_text = tiny_caps(f"""📊 **ʏᴏᴜʀ sᴛᴀᴛɪsᴛɪᴄs**

👥 **ᴍᴀᴛᴄʜᴇs ғᴏᴜɴᴅ**: {user_data.get('matches_found', 0)}
💬 **ᴍᴇssᴀɢᴇs sᴇɴᴛ**: {user_data.get('messages_sent', 0)}
⏰ **ᴛɪᴍᴇ sᴘᴇɴᴛ**: {user_data.get('time_spent', '0 ᴍɪɴᴜᴛᴇs')}
🎯 **sᴜᴄᴄᴇssғᴜʟ ᴄʜᴀᴛs**: {user_data.get('successful_chats', 0)}
⭐ **ʀᴀᴛɪɴɢ**: {user_data.get('rating', 4.5)}/5.0
🏆 **ʟᴇᴠᴇʟ**: {user_data.get('level', 1)}
🔥 **sᴛʀᴇᴀᴋ**: {user_data.get('streak', 0)} ᴅᴀʏs
🎁 **ʀᴇғᴇʀʀᴀʟs**: {user_data.get('ref_count', 0)}
💰 **ᴄᴏɪɴs**: {user_data.get('coins', 10)}
👑 **ᴘʀᴇᴍɪᴜᴍ**: {"ʏᴇs ✨" if user_data.get('premium', False) else "ɴᴏ"}""")
            else:
                stats_text = tiny_caps("❌ ɴᴏ sᴛᴀᴛɪsᴛɪᴄs ᴀᴠᴀɪʟᴀʙʟᴇ.")
            
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 ғɪɴᴅ ᴍᴏʀᴇ ᴍᴀᴛᴄʜᴇs", callback_data="menu_find")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_help":
            await callback_query.message.edit_text(
                tiny_caps("""🆘 **ʜᴇʟᴘ & sᴜᴘᴘᴏʀᴛ**

**🔸 ᴄᴏᴍᴍᴀɴᴅs:**
/start - sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ
/find - ғɪɴᴅ ᴀ ɴᴇᴡ ᴘᴀʀᴛɴᴇʀ
/profile - ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ
/wallet - ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴄᴏɪɴs
/stop - sᴛᴏᴘ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ
/report - ʀᴇᴘᴏʀᴛ ᴀ ᴜsᴇʀ

**🔸 ғᴇᴀᴛᴜʀᴇs:**
• ᴀɴᴏɴʏᴍᴏᴜs ᴄʜᴀᴛᴛɪɴɢ
• ɢᴇɴᴅᴇʀ ғɪʟᴛᴇʀs
• ʟᴏᴄᴀᴛɪᴏɴ ʙᴀsᴇᴅ ᴍᴀᴛᴄʜɪɴɢ
• ᴀɪ ᴄʜᴀᴛ ᴀssɪsᴛᴀɴᴛ
• ғʟɪʀᴛ ᴍᴏᴅᴇ

**🔸 ɴᴇᴇᴅ ʜᴇʟᴘ?**
ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴛᴇᴀᴍ!"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", callback_data="contact_support")],
                    [InlineKeyboardButton("❓ ғᴀǫ", callback_data="faq_menu")],
                    [InlineKeyboardButton("📖 ᴜsᴇʀ ɢᴜɪᴅᴇ", callback_data="user_guide")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_support":
            await callback_query.message.edit_text(
                tiny_caps("""📞 **sᴜᴘᴘᴏʀᴛ ᴄᴇɴᴛᴇʀ**

ɴᴇᴇᴅ ʜᴇʟᴘ? ᴡᴇ'ʀᴇ ʜᴇʀᴇ ғᴏʀ ʏᴏᴜ!

**📧 ᴄᴏɴᴛᴀᴄᴛ ɪɴғᴏ:**
• ᴇᴍᴀɪʟ: support@findpartner.com
• ᴛᴇʟᴇɢʀᴀᴍ: @FindPartnerSupport
• ʀᴇsᴘᴏɴsᴇ ᴛɪᴍᴇ: 24-48 ʜᴏᴜʀs

**⚡ ǫᴜɪᴄᴋ ᴀssɪsᴛᴀɴᴄᴇ:**
• ᴄʜᴇᴄᴋ ᴏᴜʀ ғᴀǫ sᴇᴄᴛɪᴏɴ
• ᴠɪsɪᴛ ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ ᴄʜᴀᴛ
• ʀᴇᴀᴅ ᴜsᴇʀ ɢᴜɪᴅᴇ"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 ᴄᴏᴍᴍᴜɴɪᴛʏ ᴄʜᴀᴛ", url="https://t.me/FindPartnerCommunity")],
                    [InlineKeyboardButton("📧 ᴇᴍᴀɪʟ sᴜᴘᴘᴏʀᴛ", callback_data="email_support")],
                    [InlineKeyboardButton("🤖 ᴄʜᴀᴛ ᴡɪᴛʜ ʙᴏᴛ", callback_data="bot_support")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_find":
            await callback_query.message.edit_text(
                tiny_caps("🔍 **Find Your Perfect Match**\n\nChoose how you want to meet people:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 ǫᴜɪᴄᴋ ᴍᴀᴛᴄʜ", callback_data="quick_match")],
                    [InlineKeyboardButton("🔧 ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ", callback_data="advanced_search")],
                    [InlineKeyboardButton("🤖 ᴄʜᴀᴛ ᴡɪᴛʜ ᴀɪ", callback_data="ai_match")],
                    [InlineKeyboardButton("💬 ғʟɪʀᴛ ᴄʜᴀᴛ", callback_data="flirt_mode")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_wallet" or data == "wallet_menu":
            user_data = users.find_one({"_id": user_id})
            coins = user_data.get("coins", 0) if user_data else 0
            premium = user_data.get("premium", False) if user_data else False
            
            wallet_text = tiny_caps(f"""
💰 **Your Wallet**

💎 **Coins**: {coins}
👑 **Status**: {"Premium ✨" if premium else "Free User"}

**💸 Coin Usage:**
• Reveal Identity: 100 coins
• Premium Upgrade: 500 coins
• Advanced Features: 30 coins
""")
            
            await callback_query.message.edit_text(
                wallet_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁 ᴅᴀɪʟʏ ʙᴏɴᴜs", callback_data="daily_bonus")],
                    [InlineKeyboardButton("💳 ʙᴜʏ ᴄᴏɪɴs", callback_data="buy_coins")],
                    [InlineKeyboardButton("🔑 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_menu")],
                    [InlineKeyboardButton("👑 ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ", callback_data="get_premium")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_referral" or data == "refer_menu":
            user_data = users.find_one({"_id": user_id})
            ref_count = user_data.get("ref_count", 0) if user_data else 0
            total_earned = ref_count * REFERRAL_COIN
            
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            
            referral_text = tiny_caps(f"""
🎁 **Referral Program** 🎁

💰 **Earn {REFERRAL_COIN} coins** for each friend you refer!

📊 **Your Stats:**
👥 **Total Referrals**: {ref_count}
💎 **Coins Earned**: {total_earned}

🔗 **Your Referral Link:**
`{ref_link}`
""")

            await callback_query.message.edit_text(
                referral_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 sʜᴀʀᴇ ʟɪɴᴋ", switch_inline_query=f"Join FindPartner Bot! {ref_link}")],
                    [InlineKeyboardButton("👥 ᴍʏ ʀᴇғᴇʀʀᴀʟs", callback_data="my_referrals")],
                    [InlineKeyboardButton("🎯 ʀᴇғᴇʀʀᴀʟ ʀᴇᴡᴀʀᴅs", callback_data="ref_rewards")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_help":
            help_text = tiny_caps("""
🆘 **Help & Support**

**🔍 How to Find Matches:**
1. Click "Find Partner" from main menu
2. Choose Quick Match or Advanced Search
3. Start chatting anonymously!

**💰 How to Earn Coins:**
• Daily bonus (5-20 coins/day)
• Refer friends (5 coins each)
• Complete profile setup

**👑 Premium Features:**
• Advanced search filters
• Priority matching
• Unlimited reveals
• See who liked you

**Need more help?**
Contact our support team!
""")
            
            await callback_query.message.edit_text(
                help_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", callback_data="menu_support")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_support":
            await callback_query.message.edit_text(
                tiny_caps("""📞 **Contact Support**

Need help or have questions?

📧 **Email**: support@findpartner.com
💬 **Telegram**: @YourSupportBot
🕐 **Response Time**: 24-48 hours

We're here to help! 😊"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url="https://t.me/YourUsername")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "menu_stats":
            user_data = users.find_one({"_id": user_id})
            if user_data:
                stats_text = tiny_caps(f"""
📊 **Your Statistics**

🎯 **Matches Found**: {user_data.get('matches_found', 0)}
💬 **Messages Sent**: {user_data.get('messages_sent', 0)}
👥 **Referrals**: {user_data.get('ref_count', 0)}
💰 **Coins Earned**: {user_data.get('ref_count', 0) * REFERRAL_COIN}
📅 **Member Since**: {user_data.get('joined_at', 'Unknown')[:10]}
🕒 **Last Active**: {user_data.get('last_active', 'Unknown')[:10]}
👑 **Premium**: {"Yes ✨" if user_data.get('premium', False) else "No"}
""")
            else:
                stats_text = tiny_caps("❌ No statistics available.")
            
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 ғɪɴᴅ ᴍᴏʀᴇ ᴍᴀᴛᴄʜᴇs", callback_data="menu_find")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        elif data == "flirt_mode":
            await callback_query.message.edit_text(
                tiny_caps("""💕 **ғʟɪʀᴛ ᴄʜᴀᴛ ᴍᴏᴅᴇ** 💕

ɢᴇᴛ ʀᴇᴀᴅʏ ғᴏʀ sᴏᴍᴇ ʀᴏᴍᴀɴᴛɪᴄ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴs! ᴛʜɪs ᴍᴏᴅᴇ ᴘʀᴏᴠɪᴅᴇs:

🌹 ᴘʀᴏғᴇssɪᴏɴᴀʟ ғʟɪʀᴛɪɴɢ ᴀssɪsᴛᴀɴᴄᴇ
💘 ʀᴏᴍᴀɴᴛɪᴄ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ sᴛᴀʀᴛᴇʀs
🔥 ᴄʜᴀʀᴍɪɴɢ ᴍᴇssᴀɢᴇ sᴜɢɢᴇsᴛɪᴏɴs
💝 ᴄᴏᴍᴘʟɪᴍᴇɴᴛ ɢᴇɴᴇʀᴀᴛᴏʀs

ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ғʟɪʀᴛ sᴛʏʟᴇ:"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("😊 sᴡᴇᴇᴛ & ʀᴏᴍᴀɴᴛɪᴄ", callback_data="flirt_sweet")],
                    [InlineKeyboardButton("😏 ᴘʟᴀʏғᴜʟ & ᴛᴇᴀsɪɴɢ", callback_data="flirt_playful")],
                    [InlineKeyboardButton("😎 ʙᴏʟᴅ & ᴄᴏɴғɪᴅᴇɴᴛ", callback_data="flirt_bold")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_menu")]
                ])
            )
        
        # Additional callback handlers for all missing buttons
        elif data == "notification_settings":
            await callback_query.message.edit_text(
                tiny_caps("🔔 **ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ sᴇᴛᴛɪɴɢs**\n\nᴄᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 ᴍᴀᴛᴄʜ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs", callback_data="toggle_match_notif")],
                    [InlineKeyboardButton("💬 ᴍᴇssᴀɢᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs", callback_data="toggle_msg_notif")],
                    [InlineKeyboardButton("🎁 ʙᴏɴᴜs ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs", callback_data="toggle_bonus_notif")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_settings")]
                ])
            )
        
        elif data == "privacy_settings":
            await callback_query.message.edit_text(
                tiny_caps("🔒 **ᴘʀɪᴠᴀᴄʏ sᴇᴛᴛɪɴɢs**\n\nᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴘʀɪᴠᴀᴄʏ ᴘʀᴇғᴇʀᴇɴᴄᴇs:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👁️ ᴘʀᴏғɪʟᴇ ᴠɪsɪʙɪʟɪᴛʏ", callback_data="profile_visibility")],
                    [InlineKeyboardButton("📱 sʜᴏᴡ ᴏɴʟɪɴᴇ sᴛᴀᴛᴜs", callback_data="toggle_online_status")],
                    [InlineKeyboardButton("🚫 ʙʟᴏᴄᴋ ʟɪsᴛ", callback_data="manage_blocked_users")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_settings")]
                ])
            )
        
        elif data == "language_settings":
            await callback_query.message.edit_text(
                tiny_caps("🌐 **ʟᴀɴɢᴜᴀɢᴇ sᴇᴛᴛɪɴɢs**\n\nᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ʟᴀɴɢᴜᴀɢᴇ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🇺🇸 ᴇɴɢʟɪsʜ", callback_data="set_lang_en")],
                    [InlineKeyboardButton("🇮🇳 ʜɪɴᴅɪ", callback_data="set_lang_hi")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_settings")]
                ])
            )
        
        elif data == "theme_settings":
            await callback_query.message.edit_text(
                tiny_caps("🎨 **ᴛʜᴇᴍᴇ sᴇᴛᴛɪɴɢs**\n\nᴄʜᴏᴏsᴇ ʏᴏᴜʀ ɪɴᴛᴇʀғᴀᴄᴇ ᴛʜᴇᴍᴇ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌙 ᴅᴀʀᴋ ᴛʜᴇᴍᴇ", callback_data="set_theme_dark")],
                    [InlineKeyboardButton("☀️ ʟɪɢʜᴛ ᴛʜᴇᴍᴇ", callback_data="set_theme_light")],
                    [InlineKeyboardButton("🌈 ᴄᴏʟᴏʀғᴜʟ", callback_data="set_theme_colorful")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_settings")]
                ])
            )
        
        elif data == "faq_menu":
            await callback_query.message.edit_text(
                tiny_caps("""❓ **ғʀᴇǫᴜᴇɴᴛʟʏ ᴀsᴋᴇᴅ ǫᴜᴇsᴛɪᴏɴs**

**Q: ʜᴏᴡ ᴅᴏ ɪ sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ?**
A: ᴄʟɪᴄᴋ "ғɪɴᴅ ᴘᴀʀᴛɴᴇʀ" ᴀɴᴅ ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴘʀᴇғᴇʀᴇɴᴄᴇ

**Q: ɪs ᴄʜᴀᴛᴛɪɴɢ ᴀɴᴏɴʏᴍᴏᴜs?**
A: ʏᴇs! ʏᴏᴜʀ ɪᴅᴇɴᴛɪᴛʏ ɪs ʜɪᴅᴅᴇɴ ᴜɴᴛɪʟ ʏᴏᴜ ᴄʜᴏᴏsᴇ ᴛᴏ ʀᴇᴠᴇᴀʟ

**Q: ʜᴏᴡ ᴅᴏ ɪ ᴇᴀʀɴ ᴄᴏɪɴs?**
A: ʀᴇғᴇʀ ғʀɪᴇɴᴅs, ᴄʟᴀɪᴍ ᴅᴀɪʟʏ ʙᴏɴᴜs, ᴏʀ ᴘᴜʀᴄʜᴀsᴇ

**Q: ᴡʜᴀᴛ ɪs ᴘʀᴇᴍɪᴜᴍ?**
A: ᴀᴅᴠᴀɴᴄᴇᴅ ғᴇᴀᴛᴜʀᴇs ʟɪᴋᴇ ғɪʟᴛᴇʀs ᴀɴᴅ ᴘʀɪᴏʀɪᴛʏ ᴍᴀᴛᴄʜɪɴɢ"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❓ ᴍᴏʀᴇ ǫᴜᴇsᴛɪᴏɴs", callback_data="more_faq")],
                    [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", callback_data="contact_support")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_help")]
                ])
            )
        
        elif data == "user_guide":
            await callback_query.message.edit_text(
                tiny_caps("""📖 **ᴜsᴇʀ ɢᴜɪᴅᴇ**

**🔸 ɢᴇᴛᴛɪɴɢ sᴛᴀʀᴛᴇᴅ:**
1. ᴄᴏᴍᴘʟᴇᴛᴇ ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ
2. ᴄʜᴏᴏsᴇ ᴍᴀᴛᴄʜɪɴɢ ᴘʀᴇғᴇʀᴇɴᴄᴇs
3. sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ!

**🔸 ᴍᴀᴛᴄʜɪɴɢ ᴛɪᴘs:**
• ʙᴇ ʀᴇsᴘᴇᴄᴛғᴜʟ ᴀɴᴅ ғʀɪᴇɴᴅʟʏ
• ᴜsᴇ ғɪʟᴛᴇʀs ғᴏʀ ʙᴇᴛᴛᴇʀ ᴍᴀᴛᴄʜᴇs
• ᴅᴏɴ'ᴛ sʜᴀʀᴇ ᴘᴇʀsᴏɴᴀʟ ɪɴғᴏ ᴛᴏᴏ ᴇᴀʀʟʏ

**🔸 sᴀғᴇᴛʏ:**
• ʀᴇᴘᴏʀᴛ ɪɴᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ʙᴇʜᴀᴠɪᴏʀ
• ʙʟᴏᴄᴋ ᴜɴᴡᴀɴᴛᴇᴅ ᴜsᴇʀs
• ɴᴇᴠᴇʀ sʜᴀʀᴇ ғɪɴᴀɴᴄɪᴀʟ ɪɴғᴏ"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛡️ sᴀғᴇᴛʏ ɢᴜɪᴅᴇ", callback_data="safety_guide")],
                    [InlineKeyboardButton("💡 ᴄʜᴀᴛᴛɪɴɢ ᴛɪᴘs", callback_data="chat_tips")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_help")]
                ])
            )
        
        elif data == "transaction_history":
            await callback_query.message.edit_text(
                tiny_caps("📊 **ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ʜɪsᴛᴏʀʏ**\n\nʏᴏᴜʀ ʀᴇᴄᴇɴᴛ ᴛʀᴀɴsᴀᴄᴛɪᴏɴs:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 ᴄᴏɪɴ ᴘᴜʀᴄʜᴀsᴇs", callback_data="coin_purchases")],
                    [InlineKeyboardButton("💸 ᴄᴏɪɴ sᴘᴇɴᴅɪɴɢ", callback_data="coin_spending")],
                    [InlineKeyboardButton("🎁 ʀᴇғᴇʀʀᴀʟ ᴇᴀʀɴɪɴɢs", callback_data="referral_earnings")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_wallet")]
                ])
            )
        
        elif data == "ref_rewards":
            await callback_query.message.edit_text(
                tiny_caps("""🎯 **ʀᴇғᴇʀʀᴀʟ ʀᴇᴡᴀʀᴅs**

**🎁 ʀᴇᴡᴀʀᴅ sʏsᴛᴇᴍ:**
• 1-5 ʀᴇғᴇʀʀᴀʟs: 5 ᴄᴏɪɴs ᴇᴀᴄʜ
• 6-10 ʀᴇғᴇʀʀᴀʟs: 7 ᴄᴏɪɴs ᴇᴀᴄʜ
• 11-20 ʀᴇғᴇʀʀᴀʟs: 10 ᴄᴏɪɴs ᴇᴀᴄʜ
• 21+ ʀᴇғᴇʀʀᴀʟs: 15 ᴄᴏɪɴs ᴇᴀᴄʜ

**🏆 sᴘᴇᴄɪᴀʟ ʙᴏɴᴜsᴇs:**
• 10 ʀᴇғᴇʀʀᴀʟs: 50 ʙᴏɴᴜs ᴄᴏɪɴs
• 25 ʀᴇғᴇʀʀᴀʟs: ғʀᴇᴇ ᴘʀᴇᴍɪᴜᴍ (1 ᴍᴏɴᴛʜ)
• 50 ʀᴇғᴇʀʀᴀʟs: ᴠɪᴘ sᴛᴀᴛᴜs

**💡 ᴛɪᴘ:** ᴛʜᴇ ᴍᴏʀᴇ ʏᴏᴜ ʀᴇғᴇʀ, ᴛʜᴇ ᴍᴏʀᴇ ʏᴏᴜ ᴇᴀʀɴ!"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 sʜᴀʀᴇ ɴᴏᴡ", callback_data="menu_referral")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_referral")]
                ])
            )
        
        # Dismiss and simple response handlers
        elif data == "dismiss":
            await callback_query.answer("ᴅɪsᴍɪssᴇᴅ! ✨", show_alert=False)
        
        elif data.startswith("set_lang_"):
            lang = data.split("_")[-1]
            await callback_query.answer(f"ʟᴀɴɢᴜᴀɢᴇ sᴇᴛ ᴛᴏ {lang.upper()} ✓", show_alert=True)
        
        elif data.startswith("set_theme_"):
            theme = data.split("_")[-1]
            await callback_query.answer(f"ᴛʜᴇᴍᴇ sᴇᴛ ᴛᴏ {theme} ✓", show_alert=True)
        
        elif data.startswith("toggle_"):
            setting = data.replace("toggle_", "").replace("_", " ")
            await callback_query.answer(f"{setting} ᴛᴏɢɢʟᴇᴅ ✓", show_alert=True)
        
        elif data == "contact_support":
            await callback_query.message.edit_text(
                tiny_caps("""📞 **ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ**

ɴᴇᴇᴅ ʜᴇʟᴘ? ᴡᴇ'ʀᴇ ʜᴇʀᴇ ᴛᴏ ᴀssɪsᴛ ʏᴏᴜ!

**📧 ᴄᴏɴᴛᴀᴄᴛ ᴏᴘᴛɪᴏɴs:**
• ᴇᴍᴀɪʟ: support@findpartner.com
• ᴛᴇʟᴇɢʀᴀᴍ: @FindPartnerSupport
• ʀᴇsᴘᴏɴsᴇ ᴛɪᴍᴇ: 24-48 ʜᴏᴜʀs

**⚡ ɪssᴜᴇ ᴄᴀᴛᴇɢᴏʀɪᴇs:**
• ᴛᴇᴄʜɴɪᴄᴀʟ ɪssᴜᴇs
• ᴘᴀʏᴍᴇɴᴛ ᴘʀᴏʙʟᴇᴍs
• ᴀᴄᴄᴏᴜɴᴛ ɪssᴜᴇs
• ғᴇᴀᴛᴜʀᴇ ʀᴇǫᴜᴇsᴛs"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 ᴄʜᴀᴛ ᴡɪᴛʜ sᴜᴘᴘᴏʀᴛ", url="https://t.me/FindPartnerSupport")],
                    [InlineKeyboardButton("📧 ᴇᴍᴀɪʟ sᴜᴘᴘᴏʀᴛ", callback_data="email_support")],
                    [InlineKeyboardButton("🤖 ᴀɪ ᴀssɪsᴛᴀɴᴛ", callback_data="bot_support")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_help")]
                ])
            )
        
        elif data == "email_support":
            await callback_query.message.edit_text(
                tiny_caps("""📧 **ᴇᴍᴀɪʟ sᴜᴘᴘᴏʀᴛ**

sᴇɴᴅ ʏᴏᴜʀ ᴅᴇᴛᴀɪʟᴇᴅ ǫᴜᴇʀʏ ᴛᴏ:
**support@findpartner.com**

**📝 ɪɴᴄʟᴜᴅᴇ ᴛʜᴇsᴇ ᴅᴇᴛᴀɪʟs:**
• ʏᴏᴜʀ ᴜsᴇʀ ɪᴅ: `{callback_query.from_user.id}`
• ᴅᴇsᴄʀɪᴘᴛɪᴏɴ ᴏғ ɪssᴜᴇ
• sᴄʀᴇᴇɴsʜᴏᴛs ɪғ ᴀᴘᴘʟɪᴄᴀʙʟᴇ
• sᴛᴇᴘs ᴛᴏ ʀᴇᴘʀᴏᴅᴜᴄᴇ

**⏰ ᴇxᴘᴇᴄᴛᴇᴅ ʀᴇsᴘᴏɴsᴇ:** 24-48 ʜᴏᴜʀs"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 ʙᴀᴄᴋ ᴛᴏ sᴜᴘᴘᴏʀᴛ", callback_data="contact_support")]
                ])
            )
        
        elif data == "bot_support":
            await callback_query.message.edit_text(
                tiny_caps("""🤖 **ᴀɪ sᴜᴘᴘᴏʀᴛ ᴀssɪsᴛᴀɴᴛ**

ɪ'ᴍ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ᴡɪᴛʜ ᴄᴏᴍᴍᴏɴ ɪssᴜᴇs:

**🔧 ᴄᴏᴍᴍᴏɴ sᴏʟᴜᴛɪᴏɴs:**
• ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ (/start)
• ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ
• ᴄʟᴇᴀʀ ᴄᴀᴄʜᴇ ᴀɴᴅ ʀᴇᴛʀʏ
• ᴜᴘᴅᴀᴛᴇ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴘᴘ

**🎯 ɪғ ɪssᴜᴇ ᴘᴇʀsɪsᴛs:**
ᴄᴏɴᴛᴀᴄᴛ ʜᴜᴍᴀɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴀɴᴜᴀʟ ᴀssɪsᴛᴀɴᴄᴇ."""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👨‍💼 ʜᴜᴍᴀɴ sᴜᴘᴘᴏʀᴛ", callback_data="contact_support")],
                    [InlineKeyboardButton("❓ ғᴀǫ", callback_data="faq_menu")]
                ])
            )
        
        elif data == "more_faq":
            await callback_query.message.edit_text(
                tiny_caps("""❓ **ᴍᴏʀᴇ ғᴀǫs**

**Q: ʜᴏᴡ ᴅᴏ ɪ ʀᴇᴘᴏʀᴛ ᴀ ᴜsᴇʀ?**
A: ᴜsᴇ ᴛʜᴇ "ʀᴇᴘᴏʀᴛ" ʙᴜᴛᴛᴏɴ ᴅᴜʀɪɴɢ ᴄʜᴀᴛ ᴏʀ /report

**Q: ᴄᴀɴ ɪ ᴄʜᴀɴɢᴇ ᴍʏ ᴀɢᴇ/ɢᴇɴᴅᴇʀ?**
A: ʏᴇs! ɢᴏ ᴛᴏ ᴘʀᴏғɪʟᴇ > ᴇᴅɪᴛ ᴘʀᴏғɪʟᴇ

**Q: ᴡʜʏ ᴀᴍ ɪ ɴᴏᴛ ɢᴇᴛᴛɪɴɢ ᴍᴀᴛᴄʜᴇs?**
A: ᴄᴏᴍᴘʟᴇᴛᴇ ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ ᴀɴᴅ ᴛʀʏ ᴅɪғғᴇʀᴇɴᴛ ғɪʟᴛᴇʀs

**Q: ʜᴏᴡ ᴛᴏ ᴜɴʙʟᴏᴄᴋ sᴏᴍᴇᴏɴᴇ?**
A: ɢᴏ ᴛᴏ sᴇᴛᴛɪɴɢs > ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs

**Q: ᴄᴀɴ ɪ ɢᴇᴛ ʀᴇғᴜɴᴅ ғᴏʀ ᴄᴏɪɴs?**
A: ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ᴡɪᴛʜ ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ᴅᴇᴛᴀɪʟs"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", callback_data="contact_support")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="faq_menu")]
                ])
            )
        
        elif data == "safety_guide":
            await callback_query.message.edit_text(
                tiny_caps("""🛡️ **sᴀғᴇᴛʏ ɢᴜɪᴅᴇ**

**🚨 sᴛᴀʏ sᴀғᴇ ᴏɴʟɪɴᴇ:**
• ɴᴇᴠᴇʀ sʜᴀʀᴇ ᴘᴇʀsᴏɴᴀʟ ɪɴғᴏ (ᴀᴅᴅʀᴇss, ᴘʜᴏɴᴇ)
• ᴅᴏɴ'ᴛ sᴇɴᴅ ᴍᴏɴᴇʏ ᴛᴏ sᴛʀᴀɴɢᴇʀs
• ᴍᴇᴇᴛ ɪɴ ᴘᴜʙʟɪᴄ ᴘʟᴀᴄᴇs ᴏɴʟʏ
• ᴛʀᴜsᴛ ʏᴏᴜʀ ɪɴsᴛɪɴᴄᴛs

**🚫 ʀᴇᴅ ғʟᴀɢs:**
• ᴀsᴋɪɴɢ ғᴏʀ ᴍᴏɴᴇʏ/ɢɪғᴛs
• ᴘʀᴇssᴜʀɪɴɢ ғᴏʀ ᴘᴇʀsᴏɴᴀʟ ɪɴғᴏ
• ɪɴᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴs
• ʀᴇғᴜsɪɴɢ ᴠɪᴅᴇᴏ ᴄᴀʟʟs

**📱 ʀᴇᴘᴏʀᴛɪɴɢ:**
ᴜsᴇ ᴛʜᴇ ʀᴇᴘᴏʀᴛ ʙᴜᴛᴛᴏɴ ɪᴍᴍᴇᴅɪᴀᴛᴇʟʏ!"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚨 ʀᴇᴘᴏʀᴛ sᴏᴍᴇᴏɴᴇ", callback_data="report_user")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="user_guide")]
                ])
            )
        
        elif data == "chat_tips":
            await callback_query.message.edit_text(
                tiny_caps("""💡 **ᴄʜᴀᴛᴛɪɴɢ ᴛɪᴘs**

**🌟 ɢʀᴇᴀᴛ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ sᴛᴀʀᴛᴇʀs:**
• "ᴡʜᴀᴛ's ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ ʜᴏʙʙʏ?"
• "ᴛᴇʟʟ ᴍᴇ sᴏᴍᴇᴛʜɪɴɢ ɪɴᴛᴇʀᴇsᴛɪɴɢ ᴀʙᴏᴜᴛ ʏᴏᴜʀsᴇʟғ"
• "ᴡʜᴀᴛ's ʏᴏᴜʀ ᴅʀᴇᴀᴍ ᴠᴀᴄᴀᴛɪᴏɴ?"

**💬 ᴋᴇᴇᴘ ɪᴛ ɪɴᴛᴇʀᴇsᴛɪɴɢ:**
• ᴀsᴋ ᴏᴘᴇɴ-ᴇɴᴅᴇᴅ ǫᴜᴇsᴛɪᴏɴs
• sʜᴀʀᴇ ғᴜɴ sᴛᴏʀɪᴇs
• ʙᴇ ɢᴇɴᴜɪɴᴇ ᴀɴᴅ ғʀɪᴇɴᴅʟʏ
• ᴜsᴇ ᴇᴍᴏᴊɪs sᴘᴀʀɪɴɢʟʏ

**❌ ᴀᴠᴏɪᴅ:**
• ᴏɴᴇ-ᴡᴏʀᴅ ʀᴇsᴘᴏɴsᴇs
• ᴛᴏᴏ ᴘᴇʀsᴏɴᴀʟ ǫᴜᴇsᴛɪᴏɴs ᴇᴀʀʟʏ
• ɴᴇɢᴀᴛɪᴠᴇ ᴛᴏᴘɪᴄs"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💕 ғʟɪʀᴛ ᴛɪᴘs", callback_data="flirt_mode")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="user_guide")]
                ])
            )
        
        elif data == "coin_purchases":
            user_data = users.find_one({"_id": user_id})
            purchase_history = user_data.get("purchase_history", []) if user_data else []
            
            if not purchase_history:
                history_text = tiny_caps("💰 **ᴄᴏɪɴ ᴘᴜʀᴄʜᴀsᴇs**\n\n❌ ɴᴏ ᴘᴜʀᴄʜᴀsᴇ ʜɪsᴛᴏʀʏ ғᴏᴜɴᴅ.")
            else:
                history_text = tiny_caps("💰 **ᴄᴏɪɴ ᴘᴜʀᴄʜᴀsᴇs**\n\n")
                for purchase in purchase_history[-5:]:  # Last 5 purchases
                    history_text += f"📅 {purchase.get('date', 'Unknown')}\n💎 +{purchase.get('amount', 0)} coins\n💳 ₹{purchase.get('price', 0)}\n\n"
            
            await callback_query.message.edit_text(
                history_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 ʙᴜʏ ᴍᴏʀᴇ", callback_data="buy_coins")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="transaction_history")]
                ])
            )
        
        elif data == "coin_spending":
            # Get spending history from transactions
            from pymongo import MongoClient
            mongo_client = MongoClient(MONGO_URL)
            transactions_db = mongo_client['find_partner']['transactions']
            spending = list(transactions_db.find({"user_id": user_id, "amount": {"$lt": 0}}).sort("timestamp", -1).limit(10))
            
            if not spending:
                spending_text = tiny_caps("💸 **ᴄᴏɪɴ sᴘᴇɴᴅɪɴɢ**\n\n❌ ɴᴏ sᴘᴇɴᴅɪɴɢ ʜɪsᴛᴏʀʏ ғᴏᴜɴᴅ.")
            else:
                spending_text = tiny_caps("💸 **ᴄᴏɪɴ sᴘᴇɴᴅɪɴɢ**\n\n")
                for transaction in spending:
                    transaction_type = transaction.get('type', 'Unknown')
                    amount = abs(transaction.get('amount', 0))
                    date = transaction.get('timestamp', 'Unknown')[:10]
                    spending_text += f"📅 {date}\n💎 -{amount} coins\n🎯 {transaction_type.replace('_', ' ').title()}\n\n"
            
            await callback_query.message.edit_text(
                spending_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 ᴇᴀʀɴ ᴍᴏʀᴇ", callback_data="daily_bonus")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="transaction_history")]
                ])
            )
        
        elif data == "referral_earnings":
            user_data = users.find_one({"_id": user_id})
            ref_count = user_data.get("ref_count", 0) if user_data else 0
            total_earned = ref_count * REFERRAL_COIN
            
            # Get referred users with timestamps
            referred_users = list(users.find({"ref_by": user_id}).sort("joined_at", -1).limit(10))
            
            earnings_text = tiny_caps(f"""🎁 **ʀᴇғᴇʀʀᴀʟ ᴇᴀʀɴɪɴɢs**

💰 **ᴛᴏᴛᴀʟ ᴇᴀʀɴᴇᴅ**: {total_earned} ᴄᴏɪɴs
👥 **ᴛᴏᴛᴀʟ ʀᴇғᴇʀʀᴀʟs**: {ref_count}

**ʀᴇᴄᴇɴᴛ ʀᴇғᴇʀʀᴀʟs:**""")
            
            if referred_users:
                for user in referred_users:
                    name = user.get("name", "Unknown")
                    date = user.get("joined_at", "Unknown")[:10]
                    earnings_text += f"\n👤 {name} - {date} (+{REFERRAL_COIN} coins)"
            else:
                earnings_text += tiny_caps("\n❌ ɴᴏ ʀᴇғᴇʀʀᴀʟs ʏᴇᴛ")
            
            await callback_query.message.edit_text(
                earnings_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 ʀᴇғᴇʀ ᴍᴏʀᴇ", callback_data="menu_referral")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="transaction_history")]
                ])
            )
        
        elif data == "manage_blocked_users":
            # Get blocked users list
            from pymongo import MongoClient
            mongo_client = MongoClient(MONGO_URL)
            blocked_db = mongo_client['find_partner']['blocked_users']
            blocked_list = list(blocked_db.find({"blocker": user_id}))
            
            if not blocked_list:
                blocked_text = tiny_caps("🚫 **ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs**\n\n✅ ɴᴏ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs")
                keyboard = [[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="privacy_settings")]]
            else:
                blocked_text = tiny_caps(f"🚫 **ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs** ({len(blocked_list)})\n\n")
                keyboard = []
                
                for blocked in blocked_list[:10]:  # Show first 10
                    blocked_id = blocked.get("blocked")
                    try:
                        blocked_user = users.find_one({"_id": blocked_id})
                        name = blocked_user.get("name", "Unknown") if blocked_user else "Unknown"
                        blocked_text += f"👤 {name}\n"
                        keyboard.append([InlineKeyboardButton(f"🔓 ᴜɴʙʟᴏᴄᴋ {name}", callback_data=f"unblock_{blocked_id}")])
                    except:
                        continue
                
                keyboard.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="privacy_settings")])
            
            await callback_query.message.edit_text(
                blocked_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data.startswith("unblock_"):
            blocked_id = int(data.replace("unblock_", ""))
            from pymongo import MongoClient
            mongo_client = MongoClient(MONGO_URL)
            blocked_db = mongo_client['find_partner']['blocked_users']
            
            result = blocked_db.delete_one({"blocker": user_id, "blocked": blocked_id})
            if result.deleted_count > 0:
                await callback_query.answer("✅ ᴜsᴇʀ ᴜɴʙʟᴏᴄᴋᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!", show_alert=True)
                # Refresh the blocked users list
                await manage_blocked_users_callback(bot, callback_query)
            else:
                await callback_query.answer("❌ ғᴀɪʟᴇᴅ ᴛᴏ ᴜɴʙʟᴏᴄᴋ ᴜsᴇʀ", show_alert=True)
        
        elif data == "profile_visibility":
            user_data = users.find_one({"_id": user_id})
            current_visibility = user_data.get("profile_visibility", "public") if user_data else "public"
            
            await callback_query.message.edit_text(
                tiny_caps(f"""👁️ **ᴘʀᴏғɪʟᴇ ᴠɪsɪʙɪʟɪᴛʏ**

ᴄᴜʀʀᴇɴᴛ sᴇᴛᴛɪɴɢ: **{current_visibility.title()}**

**ᴠɪsɪʙɪʟɪᴛʏ ᴏᴘᴛɪᴏɴs:**
• **ᴘᴜʙʟɪᴄ**: ᴇᴠᴇʀʏᴏɴᴇ ᴄᴀɴ sᴇᴇ ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ
• **ᴘʀɪᴠᴀᴛᴇ**: ᴏɴʟʏ ᴍᴀᴛᴄʜᴇᴅ ᴜsᴇʀs ᴄᴀɴ sᴇᴇ
• **ғʀɪᴇɴᴅs**: ᴏɴʟʏ ᴀᴄᴄᴇᴘᴛᴇᴅ ᴄᴏɴɴᴇᴄᴛɪᴏɴs"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 ᴘᴜʙʟɪᴄ", callback_data="set_visibility_public")],
                    [InlineKeyboardButton("🔒 ᴘʀɪᴠᴀᴛᴇ", callback_data="set_visibility_private")],
                    [InlineKeyboardButton("👥 ғʀɪᴇɴᴅs ᴏɴʟʏ", callback_data="set_visibility_friends")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="privacy_settings")]
                ])
            )
        
        elif data.startswith("set_visibility_"):
            visibility = data.replace("set_visibility_", "")
            users.update_one({"_id": user_id}, {"$set": {"profile_visibility": visibility}})
            await callback_query.answer(f"✅ ᴘʀᴏғɪʟᴇ ᴠɪsɪʙɪʟɪᴛʏ sᴇᴛ ᴛᴏ {visibility}!", show_alert=True)
        
        elif data == "age_filter":
            user_data = users.find_one({"_id": user_id})
            current_min = user_data.get("age_filter_min", 18) if user_data else 18
            current_max = user_data.get("age_filter_max", 99) if user_data else 99
            
            await callback_query.message.edit_text(
                tiny_caps(f"""🎂 **ᴀɢᴇ ʀᴀɴɢᴇ ғɪʟᴛᴇʀ**

ᴄᴜʀʀᴇɴᴛ ʀᴀɴɢᴇ: **{current_min} - {current_max} ʏᴇᴀʀs**

sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴀɢᴇ ʀᴀɴɢᴇ:"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👶 18-25", callback_data="age_range_18_25")],
                    [InlineKeyboardButton("👨 26-35", callback_data="age_range_26_35")],
                    [InlineKeyboardButton("👴 36-50", callback_data="age_range_36_50")],
                    [InlineKeyboardButton("🧓 50+", callback_data="age_range_50_99")],
                    [InlineKeyboardButton("🌐 ᴀɴʏ ᴀɢᴇ", callback_data="age_range_18_99")],
                    [InlineKeyboardButton("🔧 ᴄᴜsᴛᴏᴍ", callback_data="age_custom")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="advanced_search")]
                ])
            )
        
        elif data.startswith("age_range_"):
            age_data = data.replace("age_range_", "").split("_")
            min_age, max_age = int(age_data[0]), int(age_data[1])
            
            users.update_one(
                {"_id": user_id}, 
                {"$set": {"age_filter_min": min_age, "age_filter_max": max_age}}
            )
            await callback_query.answer(f"✅ ᴀɢᴇ ʀᴀɴɢᴇ sᴇᴛ ᴛᴏ {min_age}-{max_age}!", show_alert=True)
        
        elif data == "start_advanced_search":
            user_data = users.find_one({"_id": user_id})
            if not user_data.get("premium", False):
                return await callback_query.answer("👑 ᴘʀᴇᴍɪᴜᴍ ʀᴇǫᴜɪʀᴇᴅ!", show_alert=True)
            
            # Deduct coins for advanced search
            if user_data.get("coins", 0) < FEATURE_UNLOCK_COINS:
                return await callback_query.answer(f"💸 ɴᴇᴇᴅ {FEATURE_UNLOCK_COINS} ᴄᴏɪɴs!", show_alert=True)
            
            users.update_one({"_id": user_id}, {"$inc": {"coins": -FEATURE_UNLOCK_COINS}})
            
            # Start advanced matching logic here
            await callback_query.message.edit_text(
                tiny_caps("🔧 **ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ sᴛᴀʀᴛᴇᴅ**\n\nsᴇᴀʀᴄʜɪɴɢ ᴡɪᴛʜ ʏᴏᴜʀ ᴘʀᴇғᴇʀᴇɴᴄᴇs..."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cancel_search")]
                ])
            )
        
        elif data == "edit_profile":
            await callback_query.message.edit_text(
                tiny_caps("📝 **ᴇᴅɪᴛ ᴘʀᴏғɪʟᴇ**\n\nᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴄʜᴀɴɢᴇ?"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 ɴᴀᴍᴇ", callback_data="edit_name")],
                    [InlineKeyboardButton("🎂 ᴀɢᴇ", callback_data="edit_age")],
                    [InlineKeyboardButton("👤 ɢᴇɴᴅᴇʀ", callback_data="edit_gender")],
                    [InlineKeyboardButton("📍 ʟᴏᴄᴀᴛɪᴏɴ", callback_data="edit_location")],
                    [InlineKeyboardButton("💬 ʙɪᴏ", callback_data="edit_bio")],
                    [InlineKeyboardButton("🎯 ɪɴᴛᴇʀᴇsᴛs", callback_data="edit_interests")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_profile")]
                ])
            )
        
        elif data == "view_profile":
            user_data = users.find_one({"_id": user_id})
            if user_data:
                profile_text = tiny_caps(f"""👤 **ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ**

📝 **ɴᴀᴍᴇ**: {user_data.get('name', 'Not set')}
🎂 **ᴀɢᴇ**: {user_data.get('age', 'Not set')}
👤 **ɢᴇɴᴅᴇʀ**: {user_data.get('gender', 'Not set')}
📍 **ʟᴏᴄᴀᴛɪᴏɴ**: {user_data.get('location', 'Not set')}
💬 **ʙɪᴏ**: {user_data.get('bio', 'Not set')}
🎯 **ɪɴᴛᴇʀᴇsᴛs**: {', '.join(user_data.get('interests', [])) or 'Not set'}
🔍 **ʟᴏᴏᴋɪɴɢ ғᴏʀ**: {user_data.get('looking_for', 'Not set')}""")
            else:
                profile_text = tiny_caps("❌ ᴘʀᴏғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ.")
            
            await callback_query.message.edit_text(
                profile_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴘʀᴏғɪʟᴇ", callback_data="edit_profile")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_profile")]
                ])
            )
        
        elif data == "quick_match":
            await callback_query.message.edit_text(
                tiny_caps("🎯 **ǫᴜɪᴄᴋ ᴍᴀᴛᴄʜ**\n\nsᴇᴀʀᴄʜɪɴɢ ғᴏʀ ᴀᴠᴀɪʟᴀʙʟᴇ ᴜsᴇʀs..."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ sᴇᴀʀᴄʜ", callback_data="cancel_search")]
                ])
            )
        
        elif data == "gender_filter":
            await callback_query.message.edit_text(
                tiny_caps("🔧 **ɢᴇɴᴅᴇʀ ғɪʟᴛᴇʀ**\n\nᴄʜᴏᴏsᴇ ɢᴇɴᴅᴇʀ ᴘʀᴇғᴇʀᴇɴᴄᴇ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👨 ᴍᴀʟᴇ", callback_data="filter_male")],
                    [InlineKeyboardButton("👩 ғᴇᴍᴀʟᴇ", callback_data="filter_female")],
                    [InlineKeyboardButton("🌈 ᴀɴʏ", callback_data="filter_any")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_find")]
                ])
            )
        
        elif data == "location_filter":
            await callback_query.message.edit_text(
                tiny_caps("📍 **ʟᴏᴄᴀᴛɪᴏɴ ғɪʟᴛᴇʀ**\n\nᴄʜᴏᴏsᴇ ʟᴏᴄᴀᴛɪᴏɴ ᴘʀᴇғᴇʀᴇɴᴄᴇ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📍 sᴀᴍᴇ ʟᴏᴄᴀᴛɪᴏɴ", callback_data="filter_same_location")],
                    [InlineKeyboardButton("🌍 ᴀɴʏ ʟᴏᴄᴀᴛɪᴏɴ", callback_data="filter_any_location")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_find")]
                ])
            )
        
        elif data == "ai_match":
            await callback_query.message.edit_text(
                tiny_caps("🤖 **ᴀɪ ᴄʜᴀᴛ sᴛᴀʀᴛᴇᴅ!**\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴄʜᴀᴛᴛɪɴɢ ᴡɪᴛʜ ᴏᴜʀ ᴀɪ ᴀssɪsᴛᴀɴᴛ!\n\nsᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴛᴀʀᴛ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 sᴛᴏᴘ ᴀɪ ᴄʜᴀᴛ", callback_data="stop_ai_chat")],
                    [InlineKeyboardButton("🔄 ғɪɴᴅ ʀᴇᴀʟ ᴘᴇʀsᴏɴ", callback_data="quick_match")]
                ])
            )
        
        elif data == "advanced_search":
            user_data = users.find_one({"_id": user_id})
            if not user_data.get("premium", False):
                await callback_query.answer("👑 ᴘʀᴇᴍɪᴜᴍ ʀᴇǫᴜɪʀᴇᴅ ғᴏʀ ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ!", show_alert=True)
                return
            
            await callback_query.message.edit_text(
                tiny_caps("🔧 **ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ**\n\nᴄᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ sᴇᴀʀᴄʜ ᴘʀᴇғᴇʀᴇɴᴄᴇs:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 ɢᴇɴᴅᴇʀ ғɪʟᴛᴇʀ", callback_data="gender_filter")],
                    [InlineKeyboardButton("🎂 ᴀɢᴇ ʀᴀɴɢᴇ", callback_data="age_filter")],
                    [InlineKeyboardButton("📍 ʟᴏᴄᴀᴛɪᴏɴ", callback_data="location_filter")],
                    [InlineKeyboardButton("🎯 ɪɴᴛᴇʀᴇsᴛs", callback_data="interest_filter")],
                    [InlineKeyboardButton("🧠 ᴘᴇʀsᴏɴᴀʟɪᴛʏ", callback_data="personality_test")],
                    [InlineKeyboardButton("🔍 sᴛᴀʀᴛ sᴇᴀʀᴄʜ", callback_data="start_advanced_search")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_find")]
                ])
            )
        
        elif data == "daily_bonus":
            user_data = users.find_one({"_id": user_id})
            last_bonus = user_data.get("daily_bonus_claimed", "") if user_data else ""
            today = str(datetime.now().date())
            
            if last_bonus == today:
                await callback_query.answer("⏰ ᴅᴀɪʟʏ ʙᴏɴᴜs ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ!", show_alert=True)
                return
            
            bonus_amount = random.randint(5, 20)
            users.update_one(
                {"_id": user_id}, 
                {
                    "$inc": {"coins": bonus_amount},
                    "$set": {"daily_bonus_claimed": today}
                }
            )
            
            await callback_query.message.edit_text(
                tiny_caps(f"🎁 **ᴅᴀɪʟʏ ʙᴏɴᴜs ᴄʟᴀɪᴍᴇᴅ!**\n\n💰 +{bonus_amount} ᴄᴏɪɴs ᴀᴅᴅᴇᴅ!\n\nᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ ғᴏʀ ᴍᴏʀᴇ!"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴡᴀʟʟᴇᴛ", callback_data="menu_wallet")],
                    [InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]
                ])
            )
        
        elif data == "buy_coins":
            await callback_query.message.edit_text(
                tiny_caps("""💳 **ʙᴜʏ ᴄᴏɪɴs**

ᴄʜᴏᴏsᴇ ᴀ ᴄᴏɪɴ ᴘᴀᴄᴋᴀɢᴇ:

💎 **100 ᴄᴏɪɴs** - ₹20
💎 **500 ᴄᴏɪɴs** - ₹80 (20% ᴏғғ!)
💎 **1000 ᴄᴏɪɴs** - ₹150 (25% ᴏғғ!)
💎 **2500 ᴄᴏɪɴs** - ₹300 (40% ᴏғғ!)"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 100 ᴄᴏɪɴs - ₹20", callback_data="purchase_100")],
                    [InlineKeyboardButton("💎 500 ᴄᴏɪɴs - ₹80", callback_data="purchase_500")],
                    [InlineKeyboardButton("💎 1000 ᴄᴏɪɴs - ₹150", callback_data="purchase_1000")],
                    [InlineKeyboardButton("💎 2500 ᴄᴏɪɴs - ₹300", callback_data="purchase_2500")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_wallet")]
                ])
            )
        
        elif data.startswith("purchase_"):
            coin_amount = int(data.replace("purchase_", ""))
            prices = {100: 20, 500: 80, 1000: 150, 2500: 300}
            price = prices.get(coin_amount, 20)
            
            await callback_query.message.edit_text(
                tiny_caps(f"""💳 **ᴘᴜʀᴄʜᴀsᴇ ᴄᴏɴғɪʀᴍᴀᴛɪᴏɴ**

💎 **ᴄᴏɪɴs**: {coin_amount}
💰 **ᴘʀɪᴄᴇ**: ₹{price}

**ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅs:**
• UPI / PhonePe / GPay / Paytm
• Bank Transfer
• PayPal

ᴄᴏɴᴛᴀᴄᴛ @YourPaymentBot ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀʏᴍᴇɴᴛ"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 ᴄᴏɴᴛᴀᴄᴛ ғᴏʀ ᴘᴀʏᴍᴇɴᴛ", url="https://t.me/YourPaymentBot")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="buy_coins")]
                ])
            )
        
        elif data == "get_premium":
            user_data = users.find_one({"_id": user_id})
            current_coins = user_data.get("coins", 0) if user_data else 0
            
            if user_data.get("premium", False):
                await callback_query.answer("👑 ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴘʀᴇᴍɪᴜᴍ!", show_alert=True)
                return
            
            await callback_query.message.edit_text(
                tiny_caps(f"""👑 **ᴘʀᴇᴍɪᴜᴍ ᴜᴘɢʀᴀᴅᴇ**

💰 **ᴄᴏsᴛ**: {PREMIUM_COST} ᴄᴏɪɴs
💎 **ʏᴏᴜʀ ᴄᴏɪɴs**: {current_coins}

**🔥 ᴘʀᴇᴍɪᴜᴍ ғᴇᴀᴛᴜʀᴇs:**
• 🎯 ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ ғɪʟᴛᴇʀs
• 🔍 ᴜɴʟɪᴍɪᴛᴇᴅ ʀᴇᴠᴇᴀʟs
• ⭐ ᴘʀɪᴏʀɪᴛʏ ᴍᴀᴛᴄʜɪɴɢ
• 🧠 ᴘᴇʀsᴏɴᴀʟɪᴛʏ ᴍᴀᴛᴄʜɪɴɢ
• 💕 ғʟɪʀᴛ ᴄʜᴀᴛ ᴀssɪsᴛᴀɴᴛ
• 📊 ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɴᴀʟʏᴛɪᴄs"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👑 ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ ɴᴏᴡ!", callback_data="confirm_premium")] if current_coins >= PREMIUM_COST else [InlineKeyboardButton("💳 ʙᴜʏ ᴍᴏʀᴇ ᴄᴏɪɴs", callback_data="buy_coins")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_wallet")]
                ])
            )
        
        elif data == "confirm_premium":
            user_data = users.find_one({"_id": user_id})
            if user_data.get("coins", 0) < PREMIUM_COST:
                await callback_query.answer("💸 ɪɴsᴜғғɪᴄɪᴇɴᴛ ᴄᴏɪɴs!", show_alert=True)
                return
            
            users.update_one(
                {"_id": user_id}, 
                {
                    "$inc": {"coins": -PREMIUM_COST},
                    "$set": {"premium": True, "premium_since": str(datetime.now())}
                }
            )
            
            await callback_query.message.edit_text(
                tiny_caps("🎉 **ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs!** 🎉\n\n👑 ʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀ!\n\nᴇɴᴊᴏʏ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ғᴇᴀᴛᴜʀᴇs! ✨"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔧 ᴀᴅᴠᴀɴᴄᴇᴅ sᴇᴀʀᴄʜ", callback_data="advanced_search")],
                    [InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]
                ])
            )
        
        elif data == "my_referrals":
            referred_users = list(users.find({"ref_by": user_id}))
            if not referred_users:
                referrals_text = tiny_caps("👥 **ᴍʏ ʀᴇғᴇʀʀᴀʟs**\n\n❌ ɴᴏ ʀᴇғᴇʀʀᴀʟs ʏᴇᴛ")
            else:
                referrals_text = tiny_caps(f"👥 **ᴍʏ ʀᴇғᴇʀʀᴀʟs** ({len(referred_users)})\n\n")
                for i, ref_user in enumerate(referred_users[:10]):
                    name = ref_user.get("name", "Unknown")
                    join_date = ref_user.get("joined_at", "Unknown")[:10]
                    referrals_text += f"{i+1}. {name} - {join_date}\n"
            
            await callback_query.message.edit_text(
                referrals_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 sʜᴀʀᴇ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ", callback_data="menu_referral")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_referral")]
                ])
            )
        
        elif data.startswith("filter_"):
            filter_type = data.replace("filter_", "")
            if filter_type in ["male", "female", "any"]:
                await callback_query.answer(f"✅ ɢᴇɴᴅᴇʀ ғɪʟᴛᴇʀ sᴇᴛ: {filter_type}", show_alert=True)
                users.update_one({"_id": user_id}, {"$set": {"gender_filter": filter_type}})
            elif filter_type in ["same_location", "any_location"]:
                await callback_query.answer(f"✅ ʟᴏᴄᴀᴛɪᴏɴ ғɪʟᴛᴇʀ sᴇᴛ: {filter_type}", show_alert=True)
                users.update_one({"_id": user_id}, {"$set": {"location_filter": filter_type}})
        
        elif data == "stop_ai_chat":
            await callback_query.message.edit_text(
                tiny_caps("🤖 **ᴀɪ ᴄʜᴀᴛ sᴛᴏᴘᴘᴇᴅ**\n\nᴛʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴄʜᴀᴛᴛɪɴɢ ᴡɪᴛʜ ᴏᴜʀ ᴀɪ!"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 ғɪɴᴅ ʀᴇᴀʟ ᴘᴇʀsᴏɴ", callback_data="quick_match")],
                    [InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]
                ])
            )
        
        elif data == "redeem_menu":
            await callback_query.message.edit_text(
                tiny_caps("""🔑 **ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ**

ʜᴀᴠᴇ ᴀ ᴄᴏᴅᴇ? ᴇɴᴛᴇʀ ɪᴛ ʙᴇʟᴏᴡ!

**ʜᴏᴡ ᴛᴏ ɢᴇᴛ ᴄᴏᴅᴇs:**
• ᴘᴀʀᴛɪᴄɪᴘᴀᴛᴇ ɪɴ ᴄᴏɴᴛᴇsᴛs
• ғᴏʟʟᴏᴡ ᴏᴜʀ sᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ
• sᴘᴇᴄɪᴀʟ ᴇᴠᴇɴᴛs

sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ ʏᴏᴜʀ ᴄᴏᴅᴇ!"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_wallet")]
                ])
            )
        
        elif data == "report_user":
            await callback_query.message.edit_text(
                tiny_caps("""🚨 **ʀᴇᴘᴏʀᴛ ᴜsᴇʀ**

ᴡʜᴀᴛ ᴛʏᴘᴇ ᴏғ ɪssᴜᴇ ᴀʀᴇ ʏᴏᴜ ʀᴇᴘᴏʀᴛɪɴɢ?"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 ɪɴᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴄᴏɴᴛᴇɴᴛ", callback_data="report_inappropriate")],
                    [InlineKeyboardButton("💸 sᴄᴀᴍ/ғʀᴀᴜᴅ", callback_data="report_scam")],
                    [InlineKeyboardButton("👤 ғᴀᴋᴇ ᴘʀᴏғɪʟᴇ", callback_data="report_fake")],
                    [InlineKeyboardButton("💔 ʜᴀʀᴀssᴍᴇɴᴛ", callback_data="report_harassment")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="safety_guide")]
                ])
            )
        
        elif data.startswith("report_"):
            report_type = data.replace("report_", "")
            await callback_query.answer("✅ ʀᴇᴘᴏʀᴛ sᴜʙᴍɪᴛᴛᴇᴅ! ᴏᴜʀ ᴛᴇᴀᴍ ᴡɪʟʟ ʀᴇᴠɪᴇᴡ ɪᴛ.", show_alert=True)
        
        elif data == "interest_filter":
            await callback_query.message.edit_text(
                tiny_caps("🎯 **ɪɴᴛᴇʀᴇsᴛ ғɪʟᴛᴇʀ**\n\nᴄʜᴏᴏsᴇ ɪɴᴛᴇʀᴇsᴛs ᴛᴏ ᴍᴀᴛᴄʜ:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎵 ᴍᴜsɪᴄ", callback_data="interest_music")],
                    [InlineKeyboardButton("🎬 ᴍᴏᴠɪᴇs", callback_data="interest_movies")],
                    [InlineKeyboardButton("🏃 sᴘᴏʀᴛs", callback_data="interest_sports")],
                    [InlineKeyboardButton("📚 ʀᴇᴀᴅɪɴɢ", callback_data="interest_reading")],
                    [InlineKeyboardButton("🍳 ᴄᴏᴏᴋɪɴɢ", callback_data="interest_cooking")],
                    [InlineKeyboardButton("🎮 ɢᴀᴍɪɴɢ", callback_data="interest_gaming")],
                    [InlineKeyboardButton("✅ ᴅᴏɴᴇ", callback_data="advanced_search")]
                ])
            )
        
        elif data.startswith("interest_"):
            interest = data.replace("interest_", "")
            await callback_query.answer(f"✅ ɪɴᴛᴇʀᴇsᴛ ғɪʟᴛᴇʀ: {interest}", show_alert=True)
        
        else:
            # Default handler for unknown callbacks
            await callback_query.answer("ᴄᴏᴍɪɴɢ sᴏᴏɴ! 🚀", show_alert=True)
        
        await callback_query.answer()
        
    except Exception as e:
        LOGS.error(f"Callback error: {e}")
        try:
            await callback_query.answer(tiny_caps("❌ An error occurred. Please try again."), show_alert=True)
        except:
            pass

# Load admin commands if available
try:
    from admin import commands
except Exception as e:
    LOGS.warning(f"Admin module not loaded: {e}")

# Health check server for deployment monitoring
health_app = Flask(__name__)

@health_app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "bot": "FindPartnerBot",
        "timestamp": str(datetime.now())
    })

@health_app.route('/')
def home():
    return jsonify({
        "message": "FindPartner Bot is running!",
        "status": "active"
    })

def run_health_server():
    try:
        health_app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        LOGS.error(f"Health server error: {e}")

# Start the bot
if __name__ == "__main__":
    LOGS.info(tiny_caps("✅ Bot is starting..."))
    
    # Start health check server in background
    Thread(target=run_health_server, daemon=True).start()
    LOGS.info(tiny_caps("✅ Health check server started on port 5000"))
    
    bot.run()
