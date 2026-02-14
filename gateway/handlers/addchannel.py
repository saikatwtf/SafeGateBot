from datetime import datetime
from aiogram import types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from gateway.database import channels_collection, channel_registry
from gateway.utils.captcha import generate_short_code

class AddChannelFilter(Command):
    def __init__(self):
        super().__init__("addchannel")

async def addchannel(message: types.Message):
    args = message.text.split()[1:]
    if not args:
        await message.answer("Usage: /addchannel <channel_id>\nExample: /addchannel -1001234567890")
        return
    
    try:
        channel_id = int(args[0])
    except ValueError:
        await message.answer("Invalid channel ID. Must be a number.")
        return
    
    try:
        bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer("Bot must be an admin in the target channel.")
            return
    except Exception as e:
        await message.answer(f"Cannot access channel. Error: {str(e)}")
        return
    
    # Get channel info
    try:
        chat = await message.bot.get_chat(channel_id)
        channel_name = chat.title
    except:
        channel_name = f"Channel {channel_id}"
    
    # Register channel in registry
    await channel_registry.update_one(
        {"channel_id": channel_id, "owner_id": message.from_user.id},
        {"$set": {
            "channel_id": channel_id,
            "channel_name": channel_name,
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
        "channel_name": channel_name,
        "owner_id": message.from_user.id,
        "created_at": datetime.utcnow(),
        "stats": {"total_attempts": 0, "successful_joins": 0, "failed_captcha": 0},
        "auto_accept": False
    })
    
    bot_info = await message.bot.get_me()
    deep_link = f"https://t.me/{bot_info.username}?start={short_code}"
    
    await message.answer(f"✅ Channel added!\n\nName: {channel_name}\nShort Code: {short_code}\nDeep Link: {deep_link}")

class MyChannelsFilter(Command):
    def __init__(self):
        super().__init__("mychannels")

async def mychannels(message: types.Message):
    user_id = message.from_user.id
    
    # Get all registered channels
    registered_channels = await channel_registry.find({"owner_id": user_id}).to_list(length=100)
    
    if not registered_channels:
        await message.answer("You haven't added any channels yet.\nUse /addchannel <channel_id> to add one.")
        return
    
    builder = InlineKeyboardBuilder()
    
    for reg_channel in registered_channels:
        channel_id = reg_channel["channel_id"]
        channel_name = reg_channel["channel_name"]
        
        # Count links for this channel
        link_count = await channels_collection.count_documents({"channel_id": channel_id, "owner_id": user_id})
        
        builder.button(text=f"{channel_name} ({link_count})", callback_data=f"viewchannel_{channel_id}")
    
    builder.adjust(1)
    
    await message.answer("📋 Your Channels:", reply_markup=builder.as_markup())
