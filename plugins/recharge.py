from pyrogram import Client, filters
from config import OWNER_ID
from pymongo import MongoClient
from config import MONGO_URL, LOG_GROUP_ID

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
codes = db['redeem_codes']

# /coins - check balance
@Client.on_message(filters.command("coins") & filters.private)
async def coins(_, message):
    user = users.find_one({"_id": message.from_user.id})
    coins = user.get("coins", 0)
    await message.reply_text(f"💰 Your current balance: `{coins}` coins")

# /recharge - info
@Client.on_message(filters.command("recharge") & filters.private)
async def recharge_info(_, message):
    await message.reply_text(
        "**💸 Recharge Info**\n\n"
        "📦 100 Coins = ₹20\n"
        "📞 Pay via: UPI / Paytm\n"
        "👨‍💼 Contact Admin: @YourUsername\n\n"
        "_After payment, coins will be added manually._"
    )

# /addcoins <user_id> <amount> - admin only
@Client.on_message(filters.command("addcoins") & filters.user(OWNER_ID))
async def addcoins(_, message):
    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = int(amount)

        users.update_one({"_id": user_id}, {"$inc": {"coins": amount}})
        await message.reply_text(f"✅ Added {amount} coins to user `{user_id}`")
    except Exception as e:
        await message.reply_text("❌ Usage: /addcoins <user_id> <amount>")

# /generatecode <amount>
@Client.on_message(filters.command("generatecode") & filters.user(OWNER_ID))
async def generate_code(_, message):
    try:
        _, amount = message.text.split()
        amount = int(amount)

        import random, string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        codes.insert_one({"code": code, "amount": amount, "used": False})

        await message.reply_text(f"✅ Redeem Code Created:\n\n🔑 Code: `{code}`\n💰 Coins: {amount}")
    except:
        await message.reply_text("❌ Usage: /generatecode <amount>")

# /redeem <code>
@Client.on_message(filters.command("redeem") & filters.private)
async def redeem_code(_, message):
    try:
        _, code = message.text.split()
        data = codes.find_one({"code": code.upper()})

        if not data:
            return await message.reply_text("❌ Invalid redeem code.")

        if data["used"]:
            return await message.reply_text("⚠️ This code has already been used.")

        codes.update_one({"code": code}, {"$set": {"used": True}})
        users.update_one({"_id": message.from_user.id}, {"$inc": {"coins": data["amount"]}})
        await message.reply_text(f"🎉 Code Redeemed!\n💰 Added `{data['amount']}` coins.")

        # Log in group
        try:
            await _.send_message(
                LOG_GROUP_ID,
                f"#REDEEM\nUser: {message.from_user.mention} (`{message.from_user.id}`)\nCode: `{code}`\nCoins: {data['amount']}"
            )
        except:
            pass

    except:
        await message.reply_text("❌ Usage: /redeem <code>")