
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
profile_steps = db['profile_steps']

@Client.on_message(filters.command("profile") & filters.private)
async def view_profile_command(bot, message: Message):
    await show_profile_menu(message, message.from_user.id)

async def show_profile_menu(message, user_id):
    await message.reply(
        "👤 **Profile Management**\n\nManage your profile to get better matches:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👀 View Profile", callback_data="view_profile")],
            [InlineKeyboardButton("📝 Edit Profile", callback_data="edit_profile")],
            [InlineKeyboardButton("🎯 Matching Preferences", callback_data="match_preferences")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("view_profile"))
async def view_profile_callback(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    user = users.find_one({"_id": user_id})

    if not user:
        return await callback.answer("❌ Please use /start first.", show_alert=True)

    profile_text = f"""
👤 **Your Profile**

📝 **Name**: {user.get('name', 'Not set')}
🎂 **Age**: {user.get('age', 'Not set')}
🚻 **Gender**: {user.get('gender', 'Not set')}
📍 **Location**: {user.get('location', 'Not set')}
💬 **Bio**: {user.get('bio', 'Not set')}
🎯 **Looking for**: {user.get('looking_for', 'Not set')}
🎨 **Interests**: {', '.join(user.get('interests', [])) or 'Not set'}

📊 **Statistics**:
💰 **Coins**: {user.get('coins', 0)}
🎯 **Matches**: {user.get('matches_found', 0)}
💬 **Messages**: {user.get('messages_sent', 0)}
👑 **Premium**: {"Yes" if user.get('premium', False) else "No"}
"""

    await callback.message.edit_text(
        profile_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile")],
            [InlineKeyboardButton("🎯 Preferences", callback_data="match_preferences")],
            [InlineKeyboardButton("🔙 Back", callback_data="profile_menu")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_profile"))
async def edit_profile_callback(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "✏️ **Edit Profile**\n\nWhat would you like to update?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Name", callback_data="edit_name")],
            [InlineKeyboardButton("🎂 Age", callback_data="edit_age")],
            [InlineKeyboardButton("🚻 Gender", callback_data="edit_gender")],
            [InlineKeyboardButton("📍 Location", callback_data="edit_location")],
            [InlineKeyboardButton("💬 Bio", callback_data="edit_bio")],
            [InlineKeyboardButton("🎨 Interests", callback_data="edit_interests")],
            [InlineKeyboardButton("🔙 Back", callback_data="view_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_name"))
async def edit_name(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    profile_steps.update_one({"_id": user_id}, {"$set": {"step": "name"}}, upsert=True)
    await callback.message.edit_text(
        "📝 **Update Name**\n\nSend your new name:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_age"))
async def edit_age(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    profile_steps.update_one({"_id": user_id}, {"$set": {"step": "age"}}, upsert=True)
    await callback.message.edit_text(
        "🎂 **Update Age**\n\nSend your age (18-99):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_gender"))
async def edit_gender(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "🚻 **Select Gender**\n\nChoose your gender:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👨 Male", callback_data="gender_male")],
            [InlineKeyboardButton("👩 Female", callback_data="gender_female")],
            [InlineKeyboardButton("🌈 Other", callback_data="gender_other")],
            [InlineKeyboardButton("❌ Cancel", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("gender_(male|female|other)"))
async def set_gender(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    gender_map = {"male": "Male", "female": "Female", "other": "Other"}
    gender = gender_map[callback.matches[0].group(1)]
    
    users.update_one({"_id": user_id}, {"$set": {"gender": gender}})
    await callback.answer(f"✅ Gender updated to {gender}")
    await callback.message.edit_text(
        f"✅ **Gender Updated**\n\nYour gender has been set to: **{gender}**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Edit", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_location"))
async def edit_location(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    profile_steps.update_one({"_id": user_id}, {"$set": {"step": "location"}}, upsert=True)
    await callback.message.edit_text(
        "📍 **Update Location**\n\nSend your city/country:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_bio"))
async def edit_bio(bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    profile_steps.update_one({"_id": user_id}, {"$set": {"step": "bio"}}, upsert=True)
    await callback.message.edit_text(
        "💬 **Update Bio**\n\nWrite a short bio about yourself (max 200 characters):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("match_preferences"))
async def match_preferences(bot, callback: CallbackQuery):
    await callback.message.edit_text(
        "🎯 **Matching Preferences**\n\nSet your preferences for finding matches:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚻 Preferred Gender", callback_data="pref_gender")],
            [InlineKeyboardButton("🎂 Age Range", callback_data="pref_age")],
            [InlineKeyboardButton("📍 Location Filter", callback_data="pref_location")],
            [InlineKeyboardButton("🔙 Back", callback_data="view_profile")]
        ])
    )

# Handle text messages for profile editing
@Client.on_message(filters.text & filters.private & ~filters.command(['start', 'find', 'stop', 'profile', 'help']))
async def handle_profile_input(bot, message: Message):
    user_id = message.from_user.id
    step_data = profile_steps.find_one({"_id": user_id})
    
    if not step_data:
        return
    
    step = step_data.get("step")
    
    if step == "name":
        if len(message.text) > 50:
            return await message.reply("❌ Name too long! Please use less than 50 characters.")
        
        users.update_one({"_id": user_id}, {"$set": {"name": message.text}})
        profile_steps.delete_one({"_id": user_id})
        await message.reply(
            f"✅ **Name Updated!**\n\nYour name has been set to: **{message.text}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Edit", callback_data="edit_profile")]
            ])
        )
    
    elif step == "age":
        try:
            age = int(message.text)
            if age < 18 or age > 99:
                return await message.reply("❌ Age must be between 18 and 99.")
            
            users.update_one({"_id": user_id}, {"$set": {"age": age}})
            profile_steps.delete_one({"_id": user_id})
            await message.reply(
                f"✅ **Age Updated!**\n\nYour age has been set to: **{age}**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Edit", callback_data="edit_profile")]
                ])
            )
        except ValueError:
            await message.reply("❌ Please send a valid age number.")
    
    elif step == "location":
        if len(message.text) > 100:
            return await message.reply("❌ Location too long! Please use less than 100 characters.")
        
        users.update_one({"_id": user_id}, {"$set": {"location": message.text}})
        profile_steps.delete_one({"_id": user_id})
        await message.reply(
            f"✅ **Location Updated!**\n\nYour location has been set to: **{message.text}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Edit", callback_data="edit_profile")]
            ])
        )
    
    elif step == "bio":
        if len(message.text) > 200:
            return await message.reply("❌ Bio too long! Please use less than 200 characters.")
        
        users.update_one({"_id": user_id}, {"$set": {"bio": message.text}})
        profile_steps.delete_one({"_id": user_id})
        await message.reply(
            f"✅ **Bio Updated!**\n\nYour bio has been set to: **{message.text}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Edit", callback_data="edit_profile")]
            ])
        )
