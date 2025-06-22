
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from pymongo import MongoClient
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

client = MongoClient(MONGO_URL)
db = client['find_partner']
users = db['users']
user_states = db['user_states']

@Client.on_callback_query(filters.regex("edit_name"))
async def edit_name_callback(bot, callback):
    user_id = callback.from_user.id
    
    # Set user state
    user_states.update_one(
        {"user_id": user_id}, 
        {"$set": {"state": "editing_name", "timestamp": str(datetime.now())}}, 
        upsert=True
    )
    
    await callback.message.edit_text(
        tiny_caps("📝 **ᴇᴅɪᴛ ɴᴀᴍᴇ**\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ɴᴇᴡ ɴᴀᴍᴇ:"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_age"))
async def edit_age_callback(bot, callback):
    user_id = callback.from_user.id
    
    user_states.update_one(
        {"user_id": user_id}, 
        {"$set": {"state": "editing_age", "timestamp": str(datetime.now())}}, 
        upsert=True
    )
    
    await callback.message.edit_text(
        tiny_caps("🎂 **ᴇᴅɪᴛ ᴀɢᴇ**\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴀɢᴇ (18-99):"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_location"))
async def edit_location_callback(bot, callback):
    user_id = callback.from_user.id
    
    user_states.update_one(
        {"user_id": user_id}, 
        {"$set": {"state": "editing_location", "timestamp": str(datetime.now())}}, 
        upsert=True
    )
    
    await callback.message.edit_text(
        tiny_caps("📍 **ᴇᴅɪᴛ ʟᴏᴄᴀᴛɪᴏɴ**\n\nᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴄɪᴛʏ/sᴛᴀᴛᴇ:"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="edit_profile")]
        ])
    )

@Client.on_callback_query(filters.regex("edit_bio"))
async def edit_bio_callback(bot, callback):
    user_id = callback.from_user.id
    
    user_states.update_one(
        {"user_id": user_id}, 
        {"$set": {"state": "editing_bio", "timestamp": str(datetime.now())}}, 
        upsert=True
    )
    
    await callback.message.edit_text(
        tiny_caps("💬 **ᴇᴅɪᴛ ʙɪᴏ**\n\nᴛᴇʟʟ ᴜs ᴀʙᴏᴜᴛ ʏᴏᴜʀsᴇʟғ (ᴍᴀx 200 ᴄʜᴀʀs):"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="edit_profile")]
        ])
    )

@Client.on_message(filters.private & filters.text)
async def handle_profile_editing(bot, message: Message):
    user_id = message.from_user.id
    user_state = user_states.find_one({"user_id": user_id})
    
    if not user_state:
        return
    
    state = user_state.get("state")
    text = message.text.strip()
    
    if state == "editing_name":
        if len(text) > 50:
            await message.reply(tiny_caps("❌ ɴᴀᴍᴇ ᴛᴏᴏ ʟᴏɴɢ! ᴋᴇᴇᴘ ɪᴛ ᴜɴᴅᴇʀ 50 ᴄʜᴀʀᴀᴄᴛᴇʀs."))
            return
        
        users.update_one({"_id": user_id}, {"$set": {"name": text}})
        user_states.delete_one({"user_id": user_id})
        
        await message.reply(
            tiny_caps(f"✅ **ɴᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ!**\n\nɴᴇᴡ ɴᴀᴍᴇ: {text}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴍᴏʀᴇ", callback_data="edit_profile")],
                [InlineKeyboardButton("👀 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="view_profile")]
            ])
        )
    
    elif state == "editing_age":
        try:
            age = int(text)
            if age < 18 or age > 99:
                await message.reply(tiny_caps("❌ ᴀɢᴇ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ 18-99!"))
                return
            
            users.update_one({"_id": user_id}, {"$set": {"age": age}})
            user_states.delete_one({"user_id": user_id})
            
            await message.reply(
                tiny_caps(f"✅ **ᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ!**\n\nɴᴇᴡ ᴀɢᴇ: {age}"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴍᴏʀᴇ", callback_data="edit_profile")],
                    [InlineKeyboardButton("👀 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="view_profile")]
                ])
            )
        except ValueError:
            await message.reply(tiny_caps("❌ ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!"))
    
    elif state == "editing_location":
        if len(text) > 100:
            await message.reply(tiny_caps("❌ ʟᴏᴄᴀᴛɪᴏɴ ᴛᴏᴏ ʟᴏɴɢ!"))
            return
        
        users.update_one({"_id": user_id}, {"$set": {"location": text}})
        user_states.delete_one({"user_id": user_id})
        
        await message.reply(
            tiny_caps(f"✅ **ʟᴏᴄᴀᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!**\n\nɴᴇᴡ ʟᴏᴄᴀᴛɪᴏɴ: {text}"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴍᴏʀᴇ", callback_data="edit_profile")],
                [InlineKeyboardButton("👀 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="view_profile")]
            ])
        )
    
    elif state == "editing_bio":
        if len(text) > 200:
            await message.reply(tiny_caps("❌ ʙɪᴏ ᴛᴏᴏ ʟᴏɴɢ! ᴋᴇᴇᴘ ɪᴛ ᴜɴᴅᴇʀ 200 ᴄʜᴀʀᴀᴄᴛᴇʀs."))
            return
        
        users.update_one({"_id": user_id}, {"$set": {"bio": text}})
        user_states.delete_one({"user_id": user_id})
        
        await message.reply(
            tiny_caps("✅ **ʙɪᴏ ᴜᴘᴅᴀᴛᴇᴅ!**\n\nʏᴏᴜʀ ᴘʀᴏғɪʟᴇ ɪs ɴᴏᴡ ᴍᴏʀᴇ ᴀᴛᴛʀᴀᴄᴛɪᴠᴇ!"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 ᴇᴅɪᴛ ᴍᴏʀᴇ", callback_data="edit_profile")],
                [InlineKeyboardButton("👀 ᴠɪᴇᴡ ᴘʀᴏғɪʟᴇ", callback_data="view_profile")]
            ])
        )
