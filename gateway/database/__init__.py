from motor.motor_asyncio import AsyncIOMotorClient
from gateway.config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
channels_collection = db["channels"]
users_collection = db["users"]
channel_registry = db["channel_registry"]
