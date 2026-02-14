from datetime import datetime
from aiogram import types, F
from aiogram.filters import ChatMemberUpdatedFilter, IS_ADMIN, IS_MEMBER
from gateway.database import channels_collection, channel_registry
from gateway.utils.captcha import generate_short_code

async def bot_added_as_admin(event: types.ChatMemberUpdated):
    chat = event.chat
    new_member = event.new_chat_member
    
    # Check if bot became admin
    if new_member.status in ["administrator", "creator"]:
        # Check if already exists
        existing = await channels_collection.find_one({"channel_id": chat.id, "owner_id": event.from_user.id})
        if existing:
            return
        
        # Register channel in registry
        await channel_registry.update_one(
            {"channel_id": chat.id, "owner_id": event.from_user.id},
            {"$set": {
                "channel_id": chat.id,
                "channel_name": chat.title,
                "owner_id": event.from_user.id,
                "auto_accept": False,
                "created_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        short_code = generate_short_code()
        await channels_collection.insert_one({
            "short_code": short_code,
            "channel_id": chat.id,
            "channel_name": chat.title,
            "owner_id": event.from_user.id,
            "created_at": datetime.utcnow(),
            "stats": {"total_attempts": 0, "successful_joins": 0, "failed_captcha": 0},
            "auto_accept": False
        })
        
        bot_info = await event.bot.get_me()
        deep_link = f"https://t.me/{bot_info.username}?start={short_code}"
        
        try:
            await event.bot.send_message(
                event.from_user.id,
                f"✅ Channel automatically added!\n\n"
                f"Name: {chat.title}\n"
                f"Short Code: {short_code}\n"
                f"Deep Link: {deep_link}"
            )
        except:
            pass

async def handle_forward(message: types.Message):
    if not message.forward_from_chat:
        await message.answer("Please forward a message from your channel.")
        return
    
    forward_chat = message.forward_from_chat
    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer("Please forward from a channel or group.")
        return
    
    channel_id = forward_chat.id
    
    # Check if bot is admin
    try:
        bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer("Bot must be an admin in that channel first.")
            return
    except Exception as e:
        await message.answer(f"Cannot access channel. Make sure bot is admin there.\nError: {str(e)}")
        return
    
    # Check if already exists
    existing = await channels_collection.find_one({"channel_id": channel_id, "owner_id": message.from_user.id})
    if existing:
        await message.answer("This channel is already added!")
        return
    
    # Register channel in registry
    await channel_registry.update_one(
        {"channel_id": channel_id, "owner_id": message.from_user.id},
        {"$set": {
            "channel_id": channel_id,
            "channel_name": forward_chat.title,
            "owner_id": message.from_user.id,
            "auto_accept": False,
            "created_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    short_code = generate_short_code()
    await channels_collection.insert_one({
        "short_code": short_code,
        "channel_id": channel_id,
        "channel_name": forward_chat.title,
        "owner_id": message.from_user.id,
        "created_at": datetime.utcnow(),
        "stats": {"total_attempts": 0, "successful_joins": 0, "failed_captcha": 0},
        "auto_accept": False
    })
    
    bot_info = await message.bot.get_me()
    deep_link = f"https://t.me/{bot_info.username}?start={short_code}"
    
    await message.answer(f"✅ Channel added!\n\nName: {forward_chat.title}\nShort Code: {short_code}\nDeep Link: {deep_link}")
