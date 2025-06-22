
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import asyncio

# Logger Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGS = logging.getLogger("FindPartnerBot")

# MongoDB Setup with error check
try:
    mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    mongo.server_info()
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

def get_main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
            InlineKeyboardButton("🔍 Find Partner", callback_data="menu_find")
        ],
        [
            InlineKeyboardButton("💰 Wallet", callback_data="menu_wallet"),
            InlineKeyboardButton("🎁 Referral", callback_data="menu_referral")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
            InlineKeyboardButton("📊 Stats", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton("🆘 Help", callback_data="menu_help"),
            InlineKeyboardButton("📞 Support", callback_data="menu_support")
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
                                f"🎉 You earned {REFERRAL_COIN} coins for referring {first_name}!\n💰 Keep sharing your referral link to earn more!"
                            )
                        except:
                            pass
            except Exception as e:
                LOGS.warning(f"Referral error: {e}")

    # Update last active
    users.update_one({"_id": user_id}, {"$set": {"last_active": str(datetime.now())}})

    # Welcome message with main menu
    welcome_text = f"""
🌟 **Welcome to FindPartner Bot** 🌟

Hello {first_name}! 👋

I'm your personal matchmaking assistant. Here's what I can help you with:

🔍 **Find Partners** - Meet new people anonymously
👤 **Profile Setup** - Create an attractive profile
💰 **Earn Coins** - Get coins through referrals and daily bonuses
🎁 **Premium Features** - Unlock advanced matching features
📊 **Statistics** - Track your interactions and matches

Use the buttons below to get started! ⬇️
"""

    await message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(),
        quote=True
    )

    # Send to log group (with error handling)
    try:
        await client.send_message(
            LOG_GROUP_ID,
            f"#NEW_USER\n👤 ID: `{user_id}`\n📝 Name: [{first_name}](tg://user?id={user_id})\n📅 Joined: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    except Exception as e:
        LOGS.warning(f"Log group error: {e}")

@bot.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Main menu callbacks
    if data == "main_menu" or data == "back_menu":
        await callback_query.message.edit_text(
            f"🌟 **Welcome back!** 🌟\n\nWhat would you like to do today?",
            reply_markup=get_main_menu()
        )
    
    elif data == "menu_profile":
        await callback_query.message.edit_text(
            "👤 **Profile Management**\n\nManage your profile to get better matches:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Edit Profile", callback_data="edit_profile")],
                [InlineKeyboardButton("👀 View Profile", callback_data="view_profile")],
                [InlineKeyboardButton("🎯 Matching Preferences", callback_data="match_preferences")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "menu_find":
        await callback_query.message.edit_text(
            "🔍 **Find Your Perfect Match**\n\nChoose how you want to meet people:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Quick Match", callback_data="quick_match")],
                [InlineKeyboardButton("🔧 Advanced Search", callback_data="advanced_search")],
                [InlineKeyboardButton("🤖 Chat with AI", callback_data="ai_match")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "menu_wallet" or data == "wallet_menu":
        user_data = users.find_one({"_id": user_id})
        coins = user_data.get("coins", 0) if user_data else 0
        premium = user_data.get("premium", False) if user_data else False
        
        wallet_text = f"""
💰 **Your Wallet**

💎 **Coins**: {coins}
👑 **Status**: {"Premium ✨" if premium else "Free User"}

**💸 Coin Usage:**
• Reveal Identity: 100 coins
• Premium Upgrade: 500 coins
• Advanced Features: 30 coins
"""
        
        await callback_query.message.edit_text(
            wallet_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus")],
                [InlineKeyboardButton("💳 Buy Coins", callback_data="buy_coins")],
                [InlineKeyboardButton("🔑 Redeem Code", callback_data="redeem_menu")],
                [InlineKeyboardButton("👑 Get Premium", callback_data="get_premium")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "menu_referral" or data == "refer_menu":
        user_data = users.find_one({"_id": user_id})
        ref_count = user_data.get("ref_count", 0) if user_data else 0
        total_earned = ref_count * REFERRAL_COIN
        
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        
        referral_text = f"""
🎁 **Referral Program** 🎁

💰 **Earn {REFERRAL_COIN} coins** for each friend you refer!

📊 **Your Stats:**
👥 **Total Referrals**: {ref_count}
💎 **Coins Earned**: {total_earned}

🔗 **Your Referral Link:**
`{ref_link}`
"""

        await callback_query.message.edit_text(
            referral_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Link", switch_inline_query=f"Join FindPartner Bot! {ref_link}")],
                [InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")],
                [InlineKeyboardButton("🎯 Referral Rewards", callback_data="ref_rewards")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "menu_help":
        help_text = """
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
"""
        
        await callback_query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contact Support", callback_data="menu_support")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "menu_support":
        await callback_query.message.edit_text(
            "📞 **Contact Support**\n\n"
            "Need help or have questions?\n\n"
            "📧 **Email**: support@findpartner.com\n"
            "💬 **Telegram**: @YourSupportBot\n"
            "🕐 **Response Time**: 24-48 hours\n\n"
            "We're here to help! 😊",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourUsername")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "menu_stats":
        user_data = users.find_one({"_id": user_id})
        if user_data:
            stats_text = f"""
📊 **Your Statistics**

🎯 **Matches Found**: {user_data.get('matches_found', 0)}
💬 **Messages Sent**: {user_data.get('messages_sent', 0)}
👥 **Referrals**: {user_data.get('ref_count', 0)}
💰 **Coins Earned**: {user_data.get('ref_count', 0) * REFERRAL_COIN}
📅 **Member Since**: {user_data.get('joined_at', 'Unknown')[:10]}
🕒 **Last Active**: {user_data.get('last_active', 'Unknown')[:10]}
👑 **Premium**: {"Yes ✨" if user_data.get('premium', False) else "No"}
"""
        else:
            stats_text = "❌ No statistics available."
        
        await callback_query.message.edit_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Find More Matches", callback_data="menu_find")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_menu")]
            ])
        )
    
    elif data == "dismiss":
        await callback_query.message.delete()
    
    await callback_query.answer()

# Load admin commands if available
try:
    from admin import commands
except Exception as e:
    LOGS.warning(f"Admin module not loaded: {e}")

# Start the bot
if __name__ == "__main__":
    LOGS.info("✅ Bot is starting...")
    bot.run()
