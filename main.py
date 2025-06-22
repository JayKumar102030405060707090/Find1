
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
                tiny_caps("🌟 **Welcome back!** 🌟\n\nWhat would you like to do today?"),
                reply_markup=get_main_menu()
            )
        
        elif data == "menu_profile":
            await callback_query.message.edit_text(
                tiny_caps("👤 **Profile Management**\n\nManage your profile to get better matches:"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴘʀᴏғɪʟᴇ", callback_data="edit_profile")],
                    [InlineKeyboardButton("👀 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="view_profile")],
                    [InlineKeyboardButton("🎯 ᴍᴀᴛᴄʜɪɴɢ ᴘʀᴇғᴇʀᴇɴᴄᴇs", callback_data="match_preferences")],
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
                tiny_caps("""💕 **Flirt Chat Mode** 💕

Get ready for some romantic conversations! This mode provides:

🌹 Professional flirting assistance
💘 Romantic conversation starters
🔥 Charming message suggestions
💝 Compliment generators

Choose your flirt style:"""),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("😊 sᴡᴇᴇᴛ & ʀᴏᴍᴀɴᴛɪᴄ", callback_data="flirt_sweet")],
                    [InlineKeyboardButton("😏 ᴘʟᴀʏғᴜʟ & ᴛᴇᴀsɪɴɢ", callback_data="flirt_playful")],
                    [InlineKeyboardButton("🔥 ʙᴏʟᴅ & ᴄᴏɴғɪᴅᴇɴᴛ", callback_data="flirt_bold")],
                    [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="menu_find")]
                ])
            )
        
        elif data == "dismiss":
            await callback_query.message.delete()
        
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
