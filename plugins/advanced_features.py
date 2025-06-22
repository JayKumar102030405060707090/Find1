
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import *
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

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

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
premium_features = db['premium_features']
user_analytics = db['user_analytics']
feedback = db['feedback']
notifications = db['notifications']

# Personality compatibility system
PERSONALITY_TYPES = {
    "adventurous": ["travel", "sports", "nature", "adventure"],
    "creative": ["art", "music", "books", "writing"],
    "social": ["movies", "cooking", "gaming", "friends"],
    "intellectual": ["technology", "books", "science", "learning"],
    "romantic": ["music", "art", "movies", "poetry"]
}

COMPATIBILITY_MATRIX = {
    "adventurous": {"adventurous": 85, "creative": 70, "social": 75, "intellectual": 60, "romantic": 65},
    "creative": {"adventurous": 70, "creative": 90, "social": 80, "intellectual": 75, "romantic": 85},
    "social": {"adventurous": 75, "creative": 80, "social": 80, "intellectual": 65, "romantic": 70},
    "intellectual": {"adventurous": 60, "creative": 75, "social": 65, "intellectual": 95, "romantic": 60},
    "romantic": {"adventurous": 65, "creative": 85, "social": 70, "intellectual": 60, "romantic": 90}
}

def calculate_personality_type(interests):
    """Calculate user's personality type based on interests"""
    scores = {ptype: 0 for ptype in PERSONALITY_TYPES}
    
    for interest in interests:
        for ptype, keywords in PERSONALITY_TYPES.items():
            if interest.lower() in keywords:
                scores[ptype] += 1
    
    return max(scores, key=scores.get) if any(scores.values()) else "social"

def calculate_compatibility_score(user1_data, user2_data):
    """Calculate compatibility score between two users"""
    score = 0
    factors = 0
    
    # Age compatibility (closer ages = higher score)
    age1 = user1_data.get('age', 25)
    age2 = user2_data.get('age', 25)
    age_diff = abs(age1 - age2)
    age_score = max(0, 100 - (age_diff * 5))
    score += age_score
    factors += 1
    
    # Interest compatibility
    interests1 = set(user1_data.get('interests', []))
    interests2 = set(user2_data.get('interests', []))
    common_interests = len(interests1.intersection(interests2))
    total_interests = len(interests1.union(interests2))
    
    if total_interests > 0:
        interest_score = (common_interests / total_interests) * 100
        score += interest_score
        factors += 1
    
    # Personality compatibility
    personality1 = calculate_personality_type(user1_data.get('interests', []))
    personality2 = calculate_personality_type(user2_data.get('interests', []))
    personality_score = COMPATIBILITY_MATRIX[personality1][personality2]
    score += personality_score
    factors += 1
    
    # Location bonus (same location = +20 points)
    if user1_data.get('location') and user2_data.get('location'):
        if user1_data['location'].lower() == user2_data['location'].lower():
            score += 20
        factors += 1
    
    return int(score / factors) if factors > 0 else 50

@Client.on_callback_query(filters.regex("personality_test"))
async def personality_test(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        tiny_caps("""🧠 **ᴘᴇʀsᴏɴᴀʟɪᴛʏ ᴛᴇsᴛ**

ᴅɪsᴄᴏᴠᴇʀ ʏᴏᴜʀ ᴍᴀᴛᴄʜɪɴɢ ᴘᴇʀsᴏɴᴀʟɪᴛʏ ᴛʏᴘᴇ!

**ǫᴜᴇsᴛɪᴏɴ 1/5:**
ᴡʜᴀᴛ's ʏᴏᴜʀ ɪᴅᴇᴀʟ ᴡᴇᴇᴋᴇɴᴅ?"""),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏔️ ᴏᴜᴛᴅᴏᴏʀ ᴀᴅᴠᴇɴᴛᴜʀᴇ", callback_data="pt_q1_adventurous")],
            [InlineKeyboardButton("🎨 ᴄʀᴇᴀᴛɪᴠᴇ ᴘʀᴏᴊᴇᴄᴛ", callback_data="pt_q1_creative")],
            [InlineKeyboardButton("👥 ᴘᴀʀᴛʏ ᴡɪᴛʜ ғʀɪᴇɴᴅs", callback_data="pt_q1_social")],
            [InlineKeyboardButton("📚 ʀᴇᴀᴅɪɴɢ & ʟᴇᴀʀɴɪɴɢ", callback_data="pt_q1_intellectual")],
            [InlineKeyboardButton("💕 ʀᴏᴍᴀɴᴛɪᴄ ᴅᴀᴛᴇ", callback_data="pt_q1_romantic")]
        ])
    )

@Client.on_callback_query(filters.regex(r"pt_q(\d+)_(\w+)"))
async def handle_personality_test(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    question_num = int(callback.matches[0].group(1))
    answer = callback.matches[0].group(2)
    
    # Store answer
    test_data = premium_features.find_one({"_id": user_id, "type": "personality_test"}) or {"_id": user_id, "type": "personality_test", "answers": {}}
    test_data["answers"][f"q{question_num}"] = answer
    premium_features.update_one({"_id": user_id, "type": "personality_test"}, {"$set": test_data}, upsert=True)
    
    # Questions
    questions = [
        "ᴡʜᴀᴛ's ʏᴏᴜʀ ɪᴅᴇᴀʟ ᴡᴇᴇᴋᴇɴᴅ?",
        "ʜᴏᴡ ᴅᴏ ʏᴏᴜ ʜᴀɴᴅʟᴇ sᴛʀᴇss?",
        "ᴡʜᴀᴛ ᴍᴏᴛɪᴠᴀᴛᴇs ʏᴏᴜ ᴍᴏsᴛ?",
        "ʜᴏᴡ ᴅᴏ ʏᴏᴜ ᴘʀᴇғᴇʀ ᴛᴏ sᴘᴇɴᴅ ᴛɪᴍᴇ?",
        "ᴡʜᴀᴛ's ʏᴏᴜʀ ɪᴅᴇᴀʟ ʀᴇʟᴀᴛɪᴏɴsʜɪᴘ?"
    ]
    
    options = [
        ["🏔️ ᴏᴜᴛᴅᴏᴏʀ ᴀᴅᴠᴇɴᴛᴜʀᴇ", "🎨 ᴄʀᴇᴀᴛɪᴠᴇ ᴘʀᴏᴊᴇᴄᴛ", "👥 ᴘᴀʀᴛʏ ᴡɪᴛʜ ғʀɪᴇɴᴅs", "📚 ʀᴇᴀᴅɪɴɢ & ʟᴇᴀʀɴɪɴɢ", "💕 ʀᴏᴍᴀɴᴛɪᴄ ᴅᴀᴛᴇ"],
        ["🏃 ᴇxᴇʀᴄɪsᴇ", "🎭 ᴀʀᴛ ᴛʜᴇʀᴀᴘʏ", "😄 ᴛᴀʟᴋ ᴛᴏ ғʀɪᴇɴᴅs", "🧘 ᴍᴇᴅɪᴛᴀᴛᴇ", "💝 sᴇʟғ-ᴄᴀʀᴇ"],
        ["🏆 ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛs", "🌟 ᴄʀᴇᴀᴛɪᴠɪᴛʏ", "🤝 ʜᴇʟᴘɪɴɢ ᴏᴛʜᴇʀs", "🧠 ᴋɴᴏᴡʟᴇᴅɢᴇ", "❤️ ʟᴏᴠᴇ"],
        ["🌍 ᴛʀᴀᴠᴇʟɪɴɢ", "🎪 ᴄʀᴇᴀᴛɪɴɢ", "🎉 sᴏᴄɪᴀʟɪᴢɪɴɢ", "💻 ʟᴇᴀʀɴɪɴɢ", "💑 ʀᴏᴍᴀɴᴄᴇ"],
        ["🤝 ᴀᴅᴠᴇɴᴛᴜʀᴏᴜs", "🎨 ᴄʀᴇᴀᴛɪᴠᴇ", "😊 ғᴜɴ & ʟɪɢʜᴛ", "🤔 ᴅᴇᴇᴘ & ᴍᴇᴀɴɪɴɢғᴜʟ", "💖 ʀᴏᴍᴀɴᴛɪᴄ"]
    ]
    
    if question_num < 5:
        next_q = question_num + 1
        keyboard = []
        for i, option in enumerate(options[question_num]):
            personality_types = ["adventurous", "creative", "social", "intellectual", "romantic"]
            keyboard.append([InlineKeyboardButton(option, callback_data=f"pt_q{next_q}_{personality_types[i]}")])
        
        await callback.message.edit_text(
            tiny_caps(f"🧠 **ᴘᴇʀsᴏɴᴀʟɪᴛʏ ᴛᴇsᴛ**\n\n**ǫᴜᴇsᴛɪᴏɴ {next_q}/5:**\n{questions[question_num]}"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Calculate result
        answers = test_data["answers"]
        personality_scores = {"adventurous": 0, "creative": 0, "social": 0, "intellectual": 0, "romantic": 0}
        
        for answer_val in answers.values():
            if answer_val in personality_scores:
                personality_scores[answer_val] += 1
        
        dominant_personality = max(personality_scores, key=personality_scores.get)
        
        # Save personality type
        users.update_one({"_id": user_id}, {"$set": {"personality_type": dominant_personality}})
        
        personality_descriptions = {
            "adventurous": "🏔️ **ᴀᴅᴠᴇɴᴛᴜʀᴏᴜs ᴇxᴘʟᴏʀᴇʀ**\nʏᴏᴜ ʟᴏᴠᴇ ɴᴇᴡ ᴇxᴘᴇʀɪᴇɴᴄᴇs ᴀɴᴅ ᴛʜʀɪʟʟs!",
            "creative": "🎨 **ᴄʀᴇᴀᴛɪᴠᴇ ᴀʀᴛɪsᴛ**\nʏᴏᴜ'ʀᴇ ɪᴍᴀɢɪɴᴀᴛɪᴠᴇ ᴀɴᴅ ᴇxᴘʀᴇssɪᴠᴇ!",
            "social": "😊 **sᴏᴄɪᴀʟ ʙᴜᴛᴛᴇʀғʟʏ**\nʏᴏᴜ ᴇɴᴊᴏʏ ᴘᴇᴏᴘʟᴇ ᴀɴᴅ ᴄᴏɴɴᴇᴄᴛɪᴏɴs!",
            "intellectual": "🧠 **ɪɴᴛᴇʟʟᴇᴄᴛᴜᴀʟ ᴛʜɪɴᴋᴇʀ**\nʏᴏᴜ ᴠᴀʟᴜᴇ ᴋɴᴏᴡʟᴇᴅɢᴇ ᴀɴᴅ ᴅᴇᴇᴘ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴs!",
            "romantic": "💕 **ʀᴏᴍᴀɴᴛɪᴄ ᴅʀᴇᴀᴍᴇʀ**\nʏᴏᴜ ᴄʜᴇʀɪsʜ ʟᴏᴠᴇ ᴀɴᴅ ᴇᴍᴏᴛɪᴏɴᴀʟ ᴄᴏɴɴᴇᴄᴛɪᴏɴs!"
        }
        
        await callback.message.edit_text(
            tiny_caps(f"""✨ **ᴘᴇʀsᴏɴᴀʟɪᴛʏ ᴛᴇsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!** ✨

{personality_descriptions[dominant_personality]}

**ʏᴏᴜʀ sᴄᴏʀᴇs:**
🏔️ ᴀᴅᴠᴇɴᴛᴜʀᴏᴜs: {personality_scores['adventurous']}/5
🎨 ᴄʀᴇᴀᴛɪᴠᴇ: {personality_scores['creative']}/5
😊 sᴏᴄɪᴀʟ: {personality_scores['social']}/5
🧠 ɪɴᴛᴇʟʟᴇᴄᴛᴜᴀʟ: {personality_scores['intellectual']}/5
💕 ʀᴏᴍᴀɴᴛɪᴄ: {personality_scores['romantic']}/5

ᴛʜɪs ᴡɪʟʟ ʜᴇʟᴘ ɪᴍᴘʀᴏᴠᴇ ʏᴏᴜʀ ᴍᴀᴛᴄʜɪɴɢ!"""),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 ғɪɴᴅ ᴄᴏᴍᴘᴀᴛɪʙʟᴇ ᴍᴀᴛᴄʜᴇs", callback_data="personality_match")],
                [InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]
            ])
        )

@Client.on_callback_query(filters.regex("personality_match"))
async def personality_based_matching(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.find_one({"_id": user_id})
    
    if not user_data.get("personality_type"):
        return await callback.answer("ᴛᴀᴋᴇ ᴘᴇʀsᴏɴᴀʟɪᴛʏ ᴛᴇsᴛ ғɪʀsᴛ!", show_alert=True)
    
    # Find compatible users
    user_personality = user_data["personality_type"]
    compatible_users = []
    
    # Get all users with personality types
    all_users = users.find({"personality_type": {"$exists": True}, "_id": {"$ne": user_id}})
    
    for other_user in all_users:
        compatibility_score = calculate_compatibility_score(user_data, other_user)
        if compatibility_score >= 70:  # High compatibility threshold
            compatible_users.append({
                "user": other_user,
                "score": compatibility_score
            })
    
    # Sort by compatibility score
    compatible_users.sort(key=lambda x: x["score"], reverse=True)
    
    if not compatible_users:
        await callback.message.edit_text(
            tiny_caps("😔 **ɴᴏ ʜɪɢʜʟʏ ᴄᴏᴍᴘᴀᴛɪʙʟᴇ ᴜsᴇʀs ғᴏᴜɴᴅ**\n\nᴛʀʏ ʀᴇɢᴜʟᴀʀ ᴍᴀᴛᴄʜɪɴɢ ᴏʀ ᴇxᴘᴀɴᴅ ʏᴏᴜʀ ɪɴᴛᴇʀᴇsᴛs!"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 ʀᴇɢᴜʟᴀʀ ᴍᴀᴛᴄʜ", callback_data="quick_match")],
                [InlineKeyboardButton("📝 ᴜᴘᴅᴀᴛᴇ ɪɴᴛᴇʀᴇsᴛs", callback_data="edit_interests")]
            ])
        )
        return
    
    # Show top matches
    match_text = tiny_caps(f"💖 **ᴄᴏᴍᴘᴀᴛɪʙʟᴇ ᴍᴀᴛᴄʜᴇs ғᴏᴜɴᴅ!**\n\nғᴏᴜɴᴅ {len(compatible_users)} ʜɪɢʜʟʏ ᴄᴏᴍᴘᴀᴛɪʙʟᴇ ᴜsᴇʀs!")
    
    keyboard = []
    for i, match in enumerate(compatible_users[:5]):  # Show top 5
        user_match = match["user"]
        score = match["score"]
        name = user_match.get("name", "Anonymous")
        keyboard.append([InlineKeyboardButton(f"💕 {name} ({score}% ᴍᴀᴛᴄʜ)", callback_data=f"connect_{user_match['_id']}")])
    
    keyboard.append([InlineKeyboardButton("🔄 sʜᴏᴡ ᴍᴏʀᴇ", callback_data="show_more_matches")])
    keyboard.append([InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="main_menu")])
    
    await callback.message.edit_text(
        match_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex("feedback_system"))
async def feedback_system(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        tiny_caps("""📝 **ғᴇᴇᴅʙᴀᴄᴋ sʏsᴛᴇᴍ**

ʜᴇʟᴘ ᴜs ɪᴍᴘʀᴏᴠᴇ ᴛʜᴇ ʙᴏᴛ!

**ᴡʜᴀᴛ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ ᴅᴏ?**"""),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ ʀᴀᴛᴇ ᴀ ᴄʜᴀᴛ", callback_data="rate_chat")],
            [InlineKeyboardButton("💭 sᴇɴᴅ ғᴇᴇᴅʙᴀᴄᴋ", callback_data="send_feedback")],
            [InlineKeyboardButton("🚨 ʀᴇᴘᴏʀᴛ ɪssᴜᴇ", callback_data="report_issue")],
            [InlineKeyboardButton("💡 sᴜɢɢᴇsᴛ ғᴇᴀᴛᴜʀᴇ", callback_data="suggest_feature")],
            [InlineKeyboardButton("🏠 ʙᴀᴄᴋ", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("rate_chat"))
async def rate_chat(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        tiny_caps("⭐ **ʀᴀᴛᴇ ʏᴏᴜʀ ʟᴀsᴛ ᴄʜᴀᴛ**\n\nʜᴏᴡ ᴡᴀs ʏᴏᴜʀ ᴇxᴘᴇʀɪᴇɴᴄᴇ?"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐⭐⭐⭐⭐ ᴇxᴄᴇʟʟᴇɴᴛ", callback_data="rating_5")],
            [InlineKeyboardButton("⭐⭐⭐⭐ ɢᴏᴏᴅ", callback_data="rating_4")],
            [InlineKeyboardButton("⭐⭐⭐ ᴏᴋᴀʏ", callback_data="rating_3")],
            [InlineKeyboardButton("⭐⭐ ᴘᴏᴏʀ", callback_data="rating_2")],
            [InlineKeyboardButton("⭐ ᴛᴇʀʀɪʙʟᴇ", callback_data="rating_1")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="feedback_system")]
        ])
    )

@Client.on_callback_query(filters.regex(r"rating_(\d+)"))
async def save_rating(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    rating = int(callback.matches[0].group(1))
    
    feedback.insert_one({
        "user_id": user_id,
        "type": "chat_rating",
        "rating": rating,
        "timestamp": str(datetime.now())
    })
    
    await callback.answer(f"✅ ᴛʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ʏᴏᴜʀ {rating}-sᴛᴀʀ ʀᴀᴛɪɴɢ!", show_alert=True)
    
    # Update user rating
    user_ratings = list(feedback.find({"user_id": user_id, "type": "chat_rating"}))
    avg_rating = sum(r["rating"] for r in user_ratings) / len(user_ratings)
    users.update_one({"_id": user_id}, {"$set": {"avg_rating": round(avg_rating, 1)}})

@Client.on_message(filters.command("analytics") & filters.user(OWNER_ID))
async def bot_analytics(bot, message: Message):
    """Advanced analytics for bot owner"""
    
    # User statistics
    total_users = users.count_documents({})
    active_users = users.count_documents({"last_active": {"$gte": str((datetime.now() - timedelta(days=7)).date())}})
    premium_users = users.count_documents({"premium": True})
    
    # Matching statistics
    from pymongo import MongoClient
    mongo_client = MongoClient(MONGO_URL)
    active_chats_db = mongo_client['find_partner']['active_chats']
    total_matches = active_chats_db.count_documents({})
    
    # Revenue statistics
    transactions_db = mongo_client['find_partner']['transactions']
    coin_purchases = list(transactions_db.find({"type": "coin_purchase"}))
    total_revenue = sum(purchase.get("amount_paid", 0) for purchase in coin_purchases)
    
    # Engagement statistics
    avg_messages = users.aggregate([
        {"$group": {"_id": None, "avg_messages": {"$avg": "$messages_sent"}}}
    ])
    avg_msg_count = next(avg_messages, {}).get("avg_messages", 0)
    
    analytics_text = f"""
📊 **Bot Analytics**

👥 **Users:**
• Total Users: {total_users}
• Active (7 days): {active_users}
• Premium Users: {premium_users}
• Conversion Rate: {(premium_users/total_users*100):.1f}%

💬 **Engagement:**
• Total Matches: {total_matches}
• Avg Messages/User: {avg_msg_count:.1f}
• Match Success Rate: {(total_matches/total_users*100):.1f}%

💰 **Revenue:**
• Total Revenue: ₹{total_revenue}
• Revenue/User: ₹{(total_revenue/total_users):.2f}
• Premium ARPU: ₹{(total_revenue/premium_users if premium_users > 0 else 0):.2f}

📈 **Growth:**
• Daily New Users: {users.count_documents({"joined_at": {"$gte": str(datetime.now().date())}}) }
• Weekly Growth: {((active_users/total_users)*100):.1f}%
"""
    
    await message.reply(analytics_text)

# Smart notification system
@Client.on_callback_query(filters.regex("smart_notifications"))
async def smart_notifications(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.find_one({"_id": user_id})
    
    # Check for potential matches
    potential_matches = users.count_documents({
        "_id": {"$ne": user_id},
        "gender": user_data.get("looking_for"),
        "looking_for": user_data.get("gender"),
        "last_active": {"$gte": str((datetime.now() - timedelta(days=3)).date())}
    })
    
    # Check for new features
    last_login = datetime.fromisoformat(user_data.get("last_active", str(datetime.now())))
    days_since_login = (datetime.now() - last_login).days
    
    notification_text = tiny_caps(f"""🔔 **sᴍᴀʀᴛ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs**

📊 **ʏᴏᴜʀ ᴜᴘᴅᴀᴛᴇs:**
• {potential_matches} ɴᴇᴡ ᴘᴏᴛᴇɴᴛɪᴀʟ ᴍᴀᴛᴄʜᴇs
• {days_since_login} ᴅᴀʏs sɪɴᴄᴇ ʟᴀsᴛ ᴀᴄᴛɪᴠɪᴛʏ
• ᴘʀᴏғɪʟᴇ ᴠɪᴇᴡs: {user_data.get('profile_views', 0)}
• ᴄᴏᴍᴘᴀᴛɪʙɪʟɪᴛʏ sᴄᴏʀᴇ: {user_data.get('avg_compatibility', 75)}%

💡 **ʀᴇᴄᴏᴍᴍᴇɴᴅᴀᴛɪᴏɴs:**""")
    
    recommendations = []
    if user_data.get("coins", 0) < 50:
        recommendations.append("• ᴄʟᴀɪᴍ ᴅᴀɪʟʏ ʙᴏɴᴜs ғᴏʀ ᴍᴏʀᴇ ᴄᴏɪɴs")
    if not user_data.get("bio"):
        recommendations.append("• ᴀᴅᴅ ᴀ ʙɪᴏ ᴛᴏ ɪɴᴄʀᴇᴀsᴇ ᴍᴀᴛᴄʜ ʀᴀᴛᴇ")
    if len(user_data.get("interests", [])) < 3:
        recommendations.append("• ᴀᴅᴅ ᴍᴏʀᴇ ɪɴᴛᴇʀᴇsᴛs ғᴏʀ ʙᴇᴛᴛᴇʀ ᴍᴀᴛᴄʜɪɴɢ")
    
    if recommendations:
        notification_text += "\n" + "\n".join(recommendations)
    else:
        notification_text += "\n• ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ ʟᴏᴏᴋs ɢʀᴇᴀᴛ! ᴋᴇᴇᴘ ᴄʜᴀᴛᴛɪɴɢ!"
    
    await callback.message.edit_text(
        notification_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 ғɪɴᴅ ᴍᴀᴛᴄʜᴇs", callback_data="quick_match")],
            [InlineKeyboardButton("📝 ᴜᴘᴅᴀᴛᴇ ᴘʀᴏғɪʟᴇ", callback_data="edit_profile")],
            [InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]
        ])
    )
