from aiogram import types
from aiogram.filters import Command
from gateway.database import db, channels_collection, users_collection
from gateway.config import ADMIN_IDS

broadcast_users_collection = db["broadcast_users"]
channel_registry = db["channel_registry"]

class StatsFilter(Command):
    def __init__(self):
        super().__init__("stats")

async def stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Unauthorized.")
        return
    
    total_users = await broadcast_users_collection.count_documents({})
    total_channels = await channel_registry.count_documents({})
    total_links = await channels_collection.count_documents({})
    active_links = await channels_collection.count_documents({"used": False})
    
    stats_text = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: <code>{total_users}</code>\n"
        f"📢 Total Channels: <code>{total_channels}</code>\n"
        f"🔗 Total Links: <code>{total_links}</code>\n"
        f"✅ Active Links: <code>{active_links}</code>\n"
        f"❌ Used Links: <code>{total_links - active_links}</code>"
    )
    
    await message.answer(stats_text, parse_mode="HTML")
