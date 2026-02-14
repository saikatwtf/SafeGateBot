from datetime import datetime
from aiogram import types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from gateway.database import channels_collection, users_collection, db
from gateway.utils.captcha import generate_captcha
from gateway.utils.rate_limiter import check_rate_limit

broadcast_users_collection = db["broadcast_users"]

class StartFilter(CommandStart):
    pass

async def start(message: types.Message):
    # Save user for broadcast
    await broadcast_users_collection.update_one(
        {"user_id": message.from_user.id},
        {"$set": {
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_seen": datetime.utcnow()
        }},
        upsert=True
    )
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    if not args:
        builder = InlineKeyboardBuilder()
        builder.button(text="📚 Help", callback_data="help")
        builder.button(text="📊 My Channels", callback_data="my_channels_btn")
        builder.adjust(2)
        
        await message.answer(
            "👋 Welcome to Gateway Bot!\n\n"
            "🔒 Secure your private channels with captcha verification\n"
            "🔗 Generate unlimited deep links\n"
            "📊 Track statistics for each link\n\n"
            "Click Help to get started!",
            reply_markup=builder.as_markup()
        )
        return
    
    unique_id = args[0]
    channel_data = await channels_collection.find_one({"short_code": unique_id})
    
    if not channel_data:
        await message.answer("Invalid link. Please check and try again.")
        return
    
    user_id = message.from_user.id
    channel_id = channel_data["channel_id"]
    
    # Check rate limit
    allowed, remaining = await check_rate_limit(user_id)
    if not allowed:
        await message.answer("⚠️ Too many attempts! Please try again after 1 hour.")
        return
    
    # Update stats
    await channels_collection.update_one(
        {"short_code": unique_id},
        {"$inc": {"stats.total_attempts": 1}}
    )
    
    try:
        member = await message.bot.get_chat_member(channel_id, user_id)
        if member.status in ["member", "administrator", "creator"]:
            await message.answer("You're already a member of this channel!")
            return
    except:
        pass
    
    code, img_buf = generate_captcha()
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"captcha_code": code, "pending_channel": channel_id, "pending_short_code": unique_id, "timestamp": datetime.utcnow()}},
        upsert=True
    )
    
    await message.answer_photo(
        photo=types.BufferedInputFile(img_buf.read(), filename="captcha.png"), 
        caption=f"Solve the captcha to proceed.\nUse: /join <code>\n\n⚠️ Remaining attempts: {remaining}"
    )
