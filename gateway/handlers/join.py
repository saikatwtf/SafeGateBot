from datetime import datetime, timedelta
from aiogram import types
from aiogram.filters import Command
from gateway.database import users_collection, channels_collection
from gateway.config import ADMIN_IDS

class JoinFilter(Command):
    def __init__(self):
        super().__init__("join")

async def join(message: types.Message):
    args = message.text.split()[1:]
    if not args:
        await message.answer("Usage: /join <captcha_code>")
        return
    
    user_id = message.from_user.id
    user_code = args[0].upper()
    
    user_data = await users_collection.find_one({"user_id": user_id})
    
    if not user_data or "captcha_code" not in user_data:
        await message.answer("No pending verification. Use a deep link first.")
        return
    
    if datetime.utcnow() - user_data["timestamp"] > timedelta(minutes=10):
        await message.answer("Captcha expired. Please start again.")
        await users_collection.delete_one({"user_id": user_id})
        return
    
    channel_id = user_data["pending_channel"]
    short_code = user_data.get("pending_short_code")
    
    if user_data["captcha_code"] != user_code:
        await message.answer("Incorrect captcha. Try again.")
        # Update failed stats
        if short_code:
            await channels_collection.update_one(
                {"short_code": short_code},
                {"$inc": {"stats.failed_captcha": 1}}
            )
        return
    
    try:
        invite_link = await message.bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            expire_date=datetime.utcnow() + timedelta(minutes=10)
        )
        await message.answer(f"✅ Verification successful!\n\nYour exclusive invite link:\n{invite_link.invite_link}\n\n⚠️ This link expires in 10 minutes and works only once.")
        
        # Update successful stats
        if short_code:
            await channels_collection.update_one(
                {"short_code": short_code},
                {"$inc": {"stats.successful_joins": 1}}
            )
        
        await users_collection.delete_one({"user_id": user_id})
    except Exception as e:
        await message.answer("Error generating invite. Bot may not have admin rights in the channel.")
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(admin_id, f"⚠️ Failed to create invite for channel {channel_id}\nError: {str(e)}")
            except:
                pass
