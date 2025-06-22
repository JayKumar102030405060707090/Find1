
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
