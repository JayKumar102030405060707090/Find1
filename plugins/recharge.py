
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from pymongo import MongoClient
from datetime import datetime, date
import random
import string

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
codes = db['redeem_codes']
transactions = db['transactions']

@Client.on_message(filters.command("wallet") & filters.private)
async def wallet_command(bot, message):
    await show_wallet(message, message.from_user.id)

async def show_wallet(message, user_id):
    user = users.find_one({"_id": user_id})
    coins = user.get("coins", 0) if user else 0
    premium = user.get("premium", False) if user else False
    
    wallet_text = f"""
💰 **Your Wallet**

💎 **Balance**: {coins} coins
👑 **Status**: {"Premium ✨" if premium else "Free User"}

**💸 Coin Prices:**
• 100 coins = ₹20
• 500 coins = ₹80 (20% off!)
• 1000 coins = ₹150 (25% off!)

**🎯 Features Cost:**
• Reveal Identity: 100 coins
• Premium Upgrade: 500 coins
• Advanced Search: 30 coins per use
"""
    
    await message.reply(
        wallet_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus")],
            [InlineKeyboardButton("💳 Buy Coins", callback_data="buy_coins")],
            [InlineKeyboardButton("🔑 Redeem Code", callback_data="redeem_menu")],
            [InlineKeyboardButton("👑 Get Premium", callback_data="get_premium")],
            [InlineKeyboardButton("📊 Transaction History", callback_data="transaction_history")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("daily_bonus"))
async def daily_bonus(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user = users.find_one({"_id": user_id})
    
    today = str(date.today())
    last_bonus = user.get("daily_bonus_claimed", "")
    
    if last_bonus == today:
        await callback.answer("🎁 You've already claimed today's bonus! Come back tomorrow.", show_alert=True)
        return
    
    # Give bonus
    bonus_amount = random.randint(5, 20)
    users.update_one(
        {"_id": user_id}, 
        {
            "$inc": {"coins": bonus_amount},
            "$set": {"daily_bonus_claimed": today}
        }
    )
    
    # Record transaction
    transactions.insert_one({
        "user_id": user_id,
        "type": "daily_bonus",
        "amount": bonus_amount,
        "timestamp": str(datetime.now())
    })
    
    await callback.answer(f"🎉 Daily bonus claimed! +{bonus_amount} coins!", show_alert=True)
    
    # Update wallet display
    user = users.find_one({"_id": user_id})
    new_balance = user.get("coins", 0)
    
    await callback.message.edit_text(
        f"🎁 **Daily Bonus Claimed!**\n\n💰 You received: **{bonus_amount} coins**\n💎 New balance: **{new_balance} coins**\n\n🔄 Come back tomorrow for another bonus!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 View Wallet", callback_data="wallet_menu")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("buy_coins"))
async def buy_coins(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 **Buy Coins**\n\nChoose a coin package:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 100 coins - ₹20", callback_data="buy_100")],
            [InlineKeyboardButton("💎 500 coins - ₹80 (20% off!)", callback_data="buy_500")],
            [InlineKeyboardButton("💎 1000 coins - ₹150 (25% off!)", callback_data="buy_1000")],
            [InlineKeyboardButton("💎 Custom Amount", callback_data="buy_custom")],
            [InlineKeyboardButton("🔙 Back", callback_data="wallet_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("buy_(100|500|1000|custom)"))
async def process_purchase(bot, callback: CallbackQuery):
    package = callback.matches[0].group(1)
    
    packages = {
        "100": {"coins": 100, "price": "₹20"},
        "500": {"coins": 500, "price": "₹80"},
        "1000": {"coins": 1000, "price": "₹150"}
    }
    
    if package == "custom":
        await callback.message.edit_text(
            "💎 **Custom Purchase**\n\nContact admin for custom coin packages:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/YourUsername")],
                [InlineKeyboardButton("🔙 Back", callback_data="buy_coins")]
            ])
        )
    else:
        pkg = packages[package]
        await callback.message.edit_text(
            f"💳 **Purchase Confirmation**\n\n"
            f"💎 **Package**: {pkg['coins']} coins\n"
            f"💰 **Price**: {pkg['price']}\n\n"
            f"**Payment Methods:**\n"
            f"📱 UPI: your-upi@paytm\n"
            f"💳 Paytm: +91XXXXXXXXXX\n\n"
            f"After payment, send screenshot to admin for manual coin addition.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/YourUsername")],
                [InlineKeyboardButton("🔙 Back", callback_data="buy_coins")]
            ])
        )

@Client.on_callback_query(filters.regex("get_premium"))
async def get_premium(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user = users.find_one({"_id": user_id})
    
    if user.get("premium", False):
        await callback.answer("👑 You're already a premium user!", show_alert=True)
        return
    
    coins = user.get("coins", 0)
    
    if coins < PREMIUM_COST:
        await callback.message.edit_text(
            f"👑 **Premium Upgrade**\n\n"
            f"💎 **Cost**: {PREMIUM_COST} coins\n"
            f"💰 **Your Balance**: {coins} coins\n"
            f"❌ **Insufficient coins!**\n\n"
            f"**Premium Features:**\n"
            f"• 🔍 Advanced search filters\n"
            f"• 👁️ See who liked your profile\n"
            f"• 💬 Unlimited messages\n"
            f"• 🎯 Priority matching\n"
            f"• 📊 Detailed statistics",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Buy More Coins", callback_data="buy_coins")],
                [InlineKeyboardButton("🔙 Back", callback_data="wallet_menu")]
            ])
        )
    else:
        await callback.message.edit_text(
            f"👑 **Premium Upgrade**\n\n"
            f"💎 **Cost**: {PREMIUM_COST} coins\n"
            f"💰 **Your Balance**: {coins} coins\n\n"
            f"**Premium Features:**\n"
            f"• 🔍 Advanced search filters\n"
            f"• 👁️ See who liked your profile\n"
            f"• 💬 Unlimited messages\n"
            f"• 🎯 Priority matching\n"
            f"• 📊 Detailed statistics\n\n"
            f"Upgrade now?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Upgrade to Premium", callback_data="confirm_premium")],
                [InlineKeyboardButton("❌ Cancel", callback_data="wallet_menu")]
            ])
        )

@Client.on_callback_query(filters.regex("confirm_premium"))
async def confirm_premium(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user = users.find_one({"_id": user_id})
    
    if user.get("coins", 0) < PREMIUM_COST:
        await callback.answer("❌ Insufficient coins!", show_alert=True)
        return
    
    users.update_one(
        {"_id": user_id},
        {
            "$inc": {"coins": -PREMIUM_COST},
            "$set": {"premium": True, "premium_since": str(datetime.now())}
        }
    )
    
    # Record transaction
    transactions.insert_one({
        "user_id": user_id,
        "type": "premium_upgrade",
        "amount": -PREMIUM_COST,
        "timestamp": str(datetime.now())
    })
    
    await callback.message.edit_text(
        "🎉 **Congratulations!** 🎉\n\n"
        "👑 You are now a **Premium User**!\n\n"
        "✨ **Premium features unlocked:**\n"
        "• 🔍 Advanced search filters\n"
        "• 👁️ See who liked your profile\n"
        "• 💬 Unlimited messages\n"
        "• 🎯 Priority matching\n"
        "• 📊 Detailed statistics\n\n"
        "Enjoy your premium experience! 🌟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Start Advanced Search", callback_data="advanced_search")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

# Admin commands
@Client.on_message(filters.command("addcoins") & filters.user(OWNER_ID))
async def addcoins(_, message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            return await message.reply("❌ Usage: /addcoins <user_id> <amount>")
        
        user_id = int(parts[1])
        amount = int(parts[2])

        users.update_one({"_id": user_id}, {"$inc": {"coins": amount}})
        
        # Record transaction
        transactions.insert_one({
            "user_id": user_id,
            "type": "admin_add",
            "amount": amount,
            "admin_id": message.from_user.id,
            "timestamp": str(datetime.now())
        })
        
        await message.reply(f"✅ Added {amount} coins to user `{user_id}`")
        
        # Notify user
        try:
            await _.send_message(
                user_id,
                f"🎉 **Coins Added!**\n\n💎 You received **{amount} coins** from admin!\n💰 Check your wallet to see the updated balance."
            )
        except:
            pass
            
    except Exception as e:
        await message.reply("❌ Error adding coins. Check the format.")

@Client.on_message(filters.command("generatecode") & filters.user(OWNER_ID))
async def generate_code(_, message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply("❌ Usage: /generatecode <amount>")
        
        amount = int(parts[1])
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        codes.insert_one({
            "code": code,
            "amount": amount,
            "used": False,
            "created_by": message.from_user.id,
            "created_at": str(datetime.now())
        })

        await message.reply(
            f"✅ **Redeem Code Created**\n\n"
            f"🔑 **Code**: `{code}`\n"
            f"💰 **Coins**: {amount}\n"
            f"📅 **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    except:
        await message.reply("❌ Usage: /generatecode <amount>")

@Client.on_callback_query(filters.regex("redeem_menu"))
async def redeem_menu(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "🔑 **Redeem Code**\n\nEnter your redeem code to get free coins!\n\nSend the code in the format: `/redeem CODE123`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Wallet", callback_data="wallet_menu")]
        ])
    )

@Client.on_message(filters.command("redeem") & filters.private)
async def redeem_code(bot, message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply("❌ Usage: /redeem <code>")
        
        code = parts[1].upper()
        user_id = message.from_user.id
        
        code_data = codes.find_one({"code": code})

        if not code_data:
            return await message.reply(
                "❌ **Invalid Code**\n\nThe redeem code you entered doesn't exist.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Buy Coins Instead", callback_data="buy_coins")]
                ])
            )

        if code_data["used"]:
            return await message.reply(
                "⚠️ **Code Already Used**\n\nThis redeem code has already been used by someone else.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Buy Coins Instead", callback_data="buy_coins")]
                ])
            )

        # Redeem the code
        codes.update_one({"code": code}, {"$set": {"used": True, "used_by": user_id, "used_at": str(datetime.now())}})
        users.update_one({"_id": user_id}, {"$inc": {"coins": code_data["amount"]}})
        
        # Record transaction
        transactions.insert_one({
            "user_id": user_id,
            "type": "redeem_code",
            "amount": code_data["amount"],
            "code": code,
            "timestamp": str(datetime.now())
        })

        await message.reply(
            f"🎉 **Code Redeemed Successfully!**\n\n"
            f"💎 **Coins Added**: {code_data['amount']}\n"
            f"💰 Check your wallet to see the updated balance!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 View Wallet", callback_data="wallet_menu")],
                [InlineKeyboardButton("🔍 Find Match", callback_data="quick_match")]
            ])
        )

        # Log in group
        try:
            await bot.send_message(
                LOG_GROUP_ID,
                f"#REDEEM\n"
                f"👤 User: {message.from_user.mention} (`{user_id}`)\n"
                f"🔑 Code: `{code}`\n"
                f"💰 Coins: {code_data['amount']}"
            )
        except:
            pass

    except Exception as e:
        await message.reply("❌ Error processing redeem code.")
