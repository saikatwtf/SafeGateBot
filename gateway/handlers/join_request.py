from aiogram import types
from gateway.database import channels_collection

async def handle_join_request(update: types.ChatJoinRequest):
    chat_id = update.chat.id
    user_id = update.from_user.id
    
    # Check if channel has auto-accept enabled
    channel = await channels_collection.find_one({"channel_id": chat_id, "auto_accept": True})
    
    if channel:
        try:
            await update.approve()
        except:
            pass
