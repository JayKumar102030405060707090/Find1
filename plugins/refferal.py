
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']

@Client.on_message(filters.command("refer") & filters.private)
async def refer_command(bot, message: Message):
    await show_referral_menu(message, message.from_user.id)

async def show_referral_menu(message, user_id):
    user = users.find_one({"_id": user_id})
    ref_count = user.get("ref_count", 0) if user else 0
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

**How it works:**
1️⃣ Share your link with friends
2️⃣ They join using your link
3️⃣ You both get {REFERRAL_COIN} coins instantly!
"""

    await message.reply(
        referral_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link", switch_inline_query=f"Join FindPartner Bot and get free coins! {ref_link}")],
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_link:{user_id}")],
            [InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")],
            [InlineKeyboardButton("🎯 Referral Rewards", callback_data="ref_rewards")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex(r"copy_link:(\d+)"))
async def copy_link(bot, callback: CallbackQuery):
    user_id = int(callback.matches[0].group(1))
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    await callback.answer(f"📋 Link copied!\n{ref_link}", show_alert=True)

@Client.on_callback_query(filters.regex("my_referrals"))
async def my_referrals(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Get users referred by this user
    referred_users = list(users.find({"ref_by": user_id}))
    
    if not referred_users:
        await callback.message.edit_text(
            "👥 **My Referrals**\n\n❌ You haven't referred anyone yet.\n\nStart sharing your referral link to earn coins!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Link", callback_data="refer_menu")],
                [InlineKeyboardButton("🔙 Back", callback_data="refer_menu")]
            ])
        )
        return
    
    referral_list = "👥 **My Referrals**\n\n"
    for i, ref_user in enumerate(referred_users[:10], 1):  # Show first 10
        name = ref_user.get("name", "Unknown")
        joined = ref_user.get("joined_at", "Unknown")[:10]  # Just date
        referral_list += f"{i}. {name} - {joined}\n"
    
    if len(referred_users) > 10:
        referral_list += f"\n... and {len(referred_users) - 10} more"
    
    referral_list += f"\n\n💰 **Total Earned**: {len(referred_users) * REFERRAL_COIN} coins"
    
    await callback.message.edit_text(
        referral_list,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Refer More", callback_data="refer_menu")],
            [InlineKeyboardButton("🔙 Back", callback_data="refer_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("ref_rewards"))
async def referral_rewards(bot, callback: CallbackQuery):
    rewards_text = """
🎯 **Referral Rewards** 🎯

For every friend you refer:
• 💎 You get: 5 coins
• 💎 They get: 5 coins (welcome bonus)

**Bonus Milestones:**
🥉 5 referrals = +25 bonus coins
🥈 10 referrals = +50 bonus coins  
🥇 25 referrals = +100 bonus coins
👑 50 referrals = +250 bonus coins + Premium!

**Tips to get more referrals:**
• Share in groups and social media
• Tell friends about anonymous chatting
• Mention the free coins they'll get
• Be active and show them it's fun!
"""
    
    await callback.message.edit_text(
        rewards_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Start Referring", callback_data="refer_menu")],
            [InlineKeyboardButton("🔙 Back", callback_data="refer_menu")]
        ])
    )

# Check for milestone rewards
def check_referral_milestones(user_id):
    user = users.find_one({"_id": user_id})
    ref_count = user.get("ref_count", 0)
    
    milestones = {5: 25, 10: 50, 25: 100, 50: 250}
    
    if ref_count in milestones:
        bonus = milestones[ref_count]
        users.update_one({"_id": user_id}, {"$inc": {"coins": bonus}})
        
        # Premium for 50 referrals
        if ref_count == 50:
            users.update_one({"_id": user_id}, {"$set": {"premium": True}})
        
        return bonus, ref_count == 50
    
    return None, False
