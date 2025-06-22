
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from pymongo import MongoClient
from random import choice
import asyncio
from datetime import datetime

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

# Professional flirting responses
FLIRT_RESPONSES = {
    "sweet": [
        "Your message just made my day brighter! 🌟 How has your day been treating you?",
        "I love how thoughtful you are! 💕 What's something that made you smile today?",
        "You have such a warm energy! ☀️ What's your favorite way to spend a cozy evening?",
        "Your words are like music to my ears! 🎵 Do you have a favorite song that moves you?",
        "I find myself looking forward to your messages! 💫 What's something you're passionate about?"
    ],
    "playful": [
        "Well, aren't you quite the charmer! 😏 Think you can keep up with my wit?",
        "I see you're trying to impress me... it's working! 😉 What's your secret talent?",
        "You're dangerous with those words! 🔥 What other tricks do you have up your sleeve?",
        "I'm starting to think you might be trouble... the good kind! 😈 Prove me right!",
        "Smooth talker, eh? 😎 Let's see if your actions match your words!"
    ],
    "bold": [
        "I like your confidence! 💪 What drives your ambition?",
        "You know exactly what you want, don't you? 🔥 I respect that boldness!",
        "There's something magnetic about your energy! ⚡ What's your biggest dream?",
        "You've definitely caught my attention! 👀 What makes you so irresistible?",
        "I admire someone who goes after what they want! 💯 What's your next big move?"
    ]
}

CONVERSATION_STARTERS = [
    "If you could have dinner with anyone in history, who would it be and why? 🍽️",
    "What's the most spontaneous thing you've ever done? ✨",
    "If you could master any skill instantly, what would you choose? 🎯",
    "What's your idea of a perfect weekend? 🌅",
    "If you could live anywhere in the world, where would it be? 🌍",
    "What's something that always makes you laugh? 😄",
    "If you had a superpower, what would it be? 💫",
    "What's the best advice you've ever received? 💭",
    "What's your favorite way to unwind after a long day? 🛀",
    "If you could time travel, would you go to the past or future? ⏰"
]

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
active_chats = db['active_chats']
blocked_users = db['blocked_users']

waiting_users = {}

def is_chatting(user_id):
    return active_chats.find_one({"$or": [{"user1": user_id}, {"user2": user_id}]})

def is_blocked(user1, user2):
    return blocked_users.find_one({"$or": [
        {"blocker": user1, "blocked": user2},
        {"blocker": user2, "blocked": user1}
    ]})

@Client.on_message(filters.command("find") & filters.private)
async def find_partner(bot, message: Message):
    user_id = message.from_user.id

    if is_chatting(user_id):
        return await message.reply(
            tiny_caps("🔄 You're already in a chat!"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 sᴛᴏᴘ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ", callback_data="stop_chat")]
            ])
        )

    await message.reply(
        tiny_caps("🔍 **Find Your Match**\n\nChoose your matching preference:"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 ǫᴜɪᴄᴋ ᴍᴀᴛᴄʜ", callback_data="quick_match")],
            [InlineKeyboardButton("🔧 ɢᴇɴᴅᴇʀ ғɪʟᴛᴇʀ", callback_data="gender_filter")],
            [InlineKeyboardButton("📍 ʟᴏᴄᴀᴛɪᴏɴ ғɪʟᴛᴇʀ", callback_data="location_filter")],
            [InlineKeyboardButton("🤖 ᴄʜᴀᴛ ᴡɪᴛʜ ᴀɪ ʙᴏᴛ", callback_data="ai_match")],
            [InlineKeyboardButton("💕 ғʟɪʀᴛ ᴍᴏᴅᴇ", callback_data="flirt_mode")]
        ])
    )

@Client.on_callback_query(filters.regex("gender_filter"))
async def gender_filter_match(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "🚻 **Gender Filter**\n\nWho would you like to match with?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👨 Male", callback_data="filter_male")],
            [InlineKeyboardButton("👩 Female", callback_data="filter_female")],
            [InlineKeyboardButton("🌈 Any Gender", callback_data="filter_any")],
            [InlineKeyboardButton("🏠 Back", callback_data="menu_find")]
        ])
    )

@Client.on_callback_query(filters.regex("location_filter"))
async def location_filter_match(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.find_one({"_id": user_id})
    user_location = user_data.get("location", "Not set") if user_data else "Not set"
    
    await callback.message.edit_text(
        f"📍 **Location Filter**\n\nYour location: {user_location}\n\nChoose matching preference:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Same City/Country", callback_data="filter_same_location")],
            [InlineKeyboardButton("🌍 Any Location", callback_data="filter_any_location")],
            [InlineKeyboardButton("🏠 Back", callback_data="menu_find")]
        ])
    )

@Client.on_callback_query(filters.regex("advanced_search"))
async def advanced_search(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.find_one({"_id": user_id})
    
    if not user_data.get("premium", False):
        return await callback.message.edit_text(
            "👑 **Premium Feature**\n\nAdvanced search is only available for premium users!\n\nUpgrade to unlock:\n• Gender filters\n• Age range filters\n• Location filters\n• Interest matching",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Get Premium", callback_data="get_premium")],
                [InlineKeyboardButton("🏠 Back", callback_data="menu_find")]
            ])
        )
    
    await callback.message.edit_text(
        "🔧 **Advanced Search**\n\nCustomize your search preferences:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚻 Gender Filter", callback_data="gender_filter")],
            [InlineKeyboardButton("🎂 Age Range", callback_data="age_filter")],
            [InlineKeyboardButton("📍 Location Filter", callback_data="location_filter")],
            [InlineKeyboardButton("🎯 Start Search", callback_data="start_advanced_search")],
            [InlineKeyboardButton("🏠 Back", callback_data="menu_find")]
        ])
    )

@Client.on_callback_query(filters.regex("flirt_sweet|flirt_playful|flirt_bold"))
async def start_flirt_chat(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    flirt_style = callback.data.split("_")[1]
    
    if is_chatting(user_id):
        return await callback.answer(tiny_caps("🔄 You're already in a chat!"), show_alert=True)
    
    # Store flirt preference
    users.update_one({"_id": user_id}, {"$set": {"flirt_style": flirt_style}})
    
    # Create AI flirt chat
    active_chats.insert_one({
        "user1": user_id, 
        "user2": f"FLIRT_AI_{flirt_style.upper()}", 
        "revealed": False,
        "started_at": str(datetime.now()),
        "chat_type": "flirt"
    })
    
    style_names = {"sweet": "Sweet & Romantic", "playful": "Playful & Teasing", "bold": "Bold & Confident"}
    
    flirt_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💘 ɢᴇᴛ ғʟɪʀᴛ sᴜɢɢᴇsᴛɪᴏɴ", callback_data="get_flirt_tip")],
        [InlineKeyboardButton("🎯 ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ sᴛᴀʀᴛᴇʀ", callback_data="get_conversation_starter")],
        [InlineKeyboardButton("🚫 sᴛᴏᴘ ᴄʜᴀᴛ", callback_data="stop_chat")],
        [InlineKeyboardButton("🔄 ғɪɴᴅ ʀᴇᴀʟ ᴘᴇʀsᴏɴ", callback_data="quick_match")]
    ])
    
    welcome_msg = tiny_caps(f"""💕 **{style_names[flirt_style]} Flirt Chat Started!** 💕

I'm your personal flirting coach! I'll help you with:
🌹 Romantic conversation ideas
💘 Charming responses
🔥 Confidence boosters
💝 Sweet compliments

Start chatting and I'll respond in your chosen style!""")
    
    await callback.message.edit_text(welcome_msg, reply_markup=flirt_markup)

@Client.on_callback_query(filters.regex("get_flirt_tip"))
async def get_flirt_tip(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = users.find_one({"_id": user_id})
    flirt_style = user_data.get("flirt_style", "sweet")
    
    tip = choice(FLIRT_RESPONSES[flirt_style])
    await callback.answer(tiny_caps(f"💘 Flirt Tip: {tip}"), show_alert=True)

@Client.on_callback_query(filters.regex("get_conversation_starter"))
async def get_conversation_starter(bot, callback: CallbackQuery):
    starter = choice(CONVERSATION_STARTERS)
    await callback.answer(tiny_caps(f"🎯 Try this: {starter}"), show_alert=True)

@Client.on_callback_query(filters.regex("cancel_search"))
async def cancel_search(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in waiting_users:
        del waiting_users[user_id]
    
    await callback.message.edit_text(
        tiny_caps("❌ **Search Cancelled**\n\nYour search has been cancelled."),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 ғɪɴᴅ ɴᴇᴡ ᴍᴀᴛᴄʜ", callback_data="quick_match")],
            [InlineKeyboardButton("🏠 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("quick_match"))
async def quick_match(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if is_chatting(user_id):
        return await callback.answer("🔄 You're already in a chat!", show_alert=True)

    # Look for waiting users
    for other_id, data in list(waiting_users.items()):
        if other_id != user_id and not is_blocked(user_id, other_id):
            # Match found
            del waiting_users[other_id]
            active_chats.insert_one({
                "user1": user_id, 
                "user2": other_id, 
                "revealed": False,
                "started_at": str(datetime.now())
            })
            
            # Update match count
            users.update_one({"_id": user_id}, {"$inc": {"matches_found": 1}})
            users.update_one({"_id": other_id}, {"$inc": {"matches_found": 1}})
            
            match_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Reveal Identity (100 coins)", callback_data="reveal_request")],
                [InlineKeyboardButton("🚫 Stop Chat", callback_data="stop_chat")],
                [InlineKeyboardButton("🚨 Report User", callback_data="report_user")]
            ])
            
            await bot.send_message(
                other_id, 
                "🎯 **Match Found!** 🎯\n\nYou're now chatting anonymously.\nStart the conversation! 💬",
                reply_markup=match_markup
            )
            await callback.message.edit_text(
                "🎯 **Match Found!** 🎯\n\nYou're now chatting anonymously.\nStart the conversation! 💬",
                reply_markup=match_markup
            )
            return

    # No match found, add to waiting list
    waiting_users[user_id] = {"filter": "none", "added_at": datetime.now()}
    
    await callback.message.edit_text(
        "⏳ **Searching for Partner...**\n\n🔍 Looking for someone awesome to chat with!\n⏰ Please wait while we find your perfect match.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel Search", callback_data="cancel_search")],
            [InlineKeyboardButton("🤖 Chat with AI Instead", callback_data="ai_match")]
        ])
    )
    
    # Auto-match with AI after 30 seconds
    await asyncio.sleep(30)
    if user_id in waiting_users:
        del waiting_users[user_id]
        await ai_match_fallback(bot, user_id)

@Client.on_callback_query(filters.regex("ai_match"))
async def ai_match(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if is_chatting(user_id):
        return await callback.answer("🔄 You're already in a chat!", show_alert=True)
    
    await ai_match_fallback(bot, user_id, callback.message)

async def ai_match_fallback(bot, user_id, message=None):
    active_chats.insert_one({
        "user1": user_id, 
        "user2": "AI_BOT", 
        "revealed": False,
        "started_at": str(datetime.now())
    })
    
    ai_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Stop Chat", callback_data="stop_chat")],
        [InlineKeyboardButton("🔄 Find Real Person", callback_data="quick_match")]
    ])
    
    welcome_msg = "🤖 **AI Chat Started!** 🤖\n\nI'm your friendly AI companion! Ask me anything or just have a casual chat. 😊"
    
    if message:
        await message.edit_text(welcome_msg, reply_markup=ai_markup)
    else:
        await bot.send_message(user_id, welcome_msg, reply_markup=ai_markup)

@Client.on_callback_query(filters.regex("stop_chat"))
async def stop_chat_callback(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    chat = is_chatting(user_id)

    if chat:
        other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]
        active_chats.delete_one({"_id": chat["_id"]})
        
        if other_user != "AI_BOT":
            try:
                await bot.send_message(
                    other_user, 
                    "🚫 **Chat Ended**\n\nThe other user has left the chat.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Find New Match", callback_data="quick_match")]
                    ])
                )
            except:
                pass
        
        await callback.message.edit_text(
            "✅ **Chat Ended Successfully**\n\nThank you for using FindPartner Bot!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Find New Match", callback_data="quick_match")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ])
        )
    else:
        await callback.answer("❌ You aren't chatting with anyone currently.", show_alert=True)

@Client.on_callback_query(filters.regex("reveal_request"))
async def reveal_request(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    chat = is_chatting(user_id)

    if not chat:
        return await callback.answer("❌ You are not in a chat currently.", show_alert=True)

    user_data = users.find_one({"_id": user_id})
    if user_data.get("coins", 0) < REVEAL_COST:
        return await callback.answer(f"💸 You need at least {REVEAL_COST} coins to send reveal request.", show_alert=True)

    other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]
    
    if other_user == "AI_BOT":
        return await callback.answer("🤖 AI bot identity is already known!", show_alert=True)

    users.update_one({"_id": user_id}, {"$inc": {"coins": -REVEAL_COST}})
    
    await bot.send_message(
        other_user,
        f"👁️ **Identity Reveal Request**\n\nSomeone wants to reveal identities!\nCost: {REVEAL_COST} coins each",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept & Reveal", callback_data=f"reveal_accept:{user_id}")],
            [InlineKeyboardButton("❌ Decline", callback_data=f"reveal_decline:{user_id}")]
        ])
    )
    
    await callback.answer("🕵️ Reveal request sent! Waiting for their response...")

@Client.on_callback_query(filters.regex(r"reveal_accept:(\d+)"))
async def reveal_accept(bot, callback: CallbackQuery):
    requester_id = int(callback.matches[0].group(1))
    user_id = callback.from_user.id

    chat = is_chatting(user_id)
    if not chat:
        return await callback.answer("❌ Chat session expired.", show_alert=True)

    user_data = users.find_one({"_id": user_id})
    if user_data.get("coins", 0) < REVEAL_COST:
        return await callback.answer(f"💸 You need {REVEAL_COST} coins to accept.", show_alert=True)

    users.update_one({"_id": user_id}, {"$inc": {"coins": -REVEAL_COST}})

    # Get user profiles
    try:
        requester = await bot.get_users(requester_id)
        accepter = await bot.get_users(user_id)

        requester_profile = users.find_one({"_id": requester_id})
        accepter_profile = users.find_one({"_id": user_id})

        reveal_info1 = f"""
🎉 **Identity Revealed!** 🎉

👤 **Name**: {accepter.first_name}
📱 **Username**: @{accepter.username or 'Hidden'}
🎂 **Age**: {accepter_profile.get('age', 'Not set')}
🚻 **Gender**: {accepter_profile.get('gender', 'Not set')}
📍 **Location**: {accepter_profile.get('location', 'Not set')}
📝 **Bio**: {accepter_profile.get('bio', 'No bio available')}
"""

        reveal_info2 = f"""
🎉 **Identity Revealed!** 🎉

👤 **Name**: {requester.first_name}
📱 **Username**: @{requester.username or 'Hidden'}
🎂 **Age**: {requester_profile.get('age', 'Not set')}
🚻 **Gender**: {requester_profile.get('gender', 'Not set')}
📍 **Location**: {requester_profile.get('location', 'Not set')}
📝 **Bio**: {requester_profile.get('bio', 'No bio available')}
"""

        await bot.send_message(requester_id, reveal_info1)
        await bot.send_message(user_id, reveal_info2)

        await callback.answer("✅ Identities revealed successfully!")
        
    except Exception as e:
        await callback.answer("❌ Error revealing identities.", show_alert=True)

# Message forwarding between matched users
@Client.on_message(filters.private & filters.text & ~filters.command(['start', 'find', 'stop', 'profile', 'help']))
async def forward_messages(bot, message: Message):
    user_id = message.from_user.id
    chat = is_chatting(user_id)

    if not chat:
        return

    partner_id = chat["user1"] if chat["user2"] == user_id else chat["user2"]
    
    # Update message count
    users.update_one({"_id": user_id}, {"$inc": {"messages_sent": 1}})

    if partner_id == "AI_BOT":
        # AI Response
        await asyncio.sleep(1)  # Simulate typing
        ai_response = choice(AI_RESPONSES)
        await message.reply(tiny_caps(f"🤖 **AI**: {ai_response}"))
    elif partner_id.startswith("FLIRT_AI_"):
        # Flirt AI Response
        await asyncio.sleep(2)  # Simulate typing
        user_data = users.find_one({"_id": user_id})
        flirt_style = user_data.get("flirt_style", "sweet")
        
        flirt_response = choice(FLIRT_RESPONSES[flirt_style])
        await message.reply(tiny_caps(f"💕 **Flirt Coach**: {flirt_response}"))
        
        # Sometimes add conversation starters
        if len(message.text) < 20:  # Short messages get extra help
            await asyncio.sleep(1)
            starter = choice(CONVERSATION_STARTERS)
            await message.reply(tiny_caps(f"💡 **Tip**: Try asking: {starter}"))
    else:
        # Forward to real user
        try:
            await bot.send_message(
                partner_id,
                tiny_caps(f"💬 **Anonymous**: {message.text}"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👁️ ʀᴇᴠᴇᴀʟ (100 ᴄᴏɪɴs)", callback_data="reveal_request")],
                    [InlineKeyboardButton("🚫 sᴛᴏᴘ", callback_data="stop_chat")]
                ])
            )
        except Exception as e:
            await message.reply(tiny_caps("❌ Failed to send message. The other user might have left."))
            active_chats.delete_one({"_id": chat["_id"]})

@Client.on_message(filters.command("stop") & filters.private)
async def stop_chat_command(bot, message: Message):
    user_id = message.from_user.id
    chat = is_chatting(user_id)

    if chat:
        other_user = chat["user1"] if chat["user2"] == user_id else chat["user2"]
        active_chats.delete_one({"_id": chat["_id"]})
        
        if other_user != "AI_BOT":
            try:
                await bot.send_message(other_user, "🚫 The other user has left the chat.")
            except:
                pass
        
        await message.reply(
            "✅ Chat ended successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Find New Match", callback_data="quick_match")]
            ])
        )
    else:
        await message.reply("❌ You aren't chatting with anyone currently.")
