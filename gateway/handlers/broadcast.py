from aiogram import types
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from gateway.database import db
from gateway.config import ADMIN_IDS
import time

broadcast_users_collection = db["broadcast_users"]

class BroadcastFilter(Command):
    def __init__(self):
        super().__init__("broadcast")

async def broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Unauthorized.")
        return
    
    if not message.reply_to_message:
        await message.answer("Reply to a message to broadcast it.")
        return
    
    users = await broadcast_users_collection.find({}).to_list(length=None)
    total = len(users)
    
    status_msg = await message.answer(f"Broadcasting to {total} users...")
    start_time = time.time()
    
    success = blocked = deleted = failed = 0
    
    for i, user in enumerate(users, 1):
        try:
            await message.reply_to_message.copy_to(user["user_id"])
            success += 1
        except TelegramForbiddenError:
            blocked += 1
        except TelegramBadRequest:
            deleted += 1
        except:
            failed += 1
        
        if i % 20 == 0 or i == total:
            await status_msg.edit_text(
                f"Broadcasting...\n\n"
                f"Progress: {i}/{total}\n"
                f"✅ Success: {success}\n"
                f"🚫 Blocked: {blocked}\n"
                f"❌ Deleted: {deleted}\n"
                f"⚠️ Failed: {failed}"
            )
    
    elapsed = int(time.time() - start_time)
    await status_msg.edit_text(
        f"✅ Broadcast Completed in {elapsed}s\n\n"
        f"Total: {total}\n"
        f"✅ Success: {success}\n"
        f"🚫 Blocked: {blocked}\n"
        f"❌ Deleted: {deleted}\n"
        f"⚠️ Failed: {failed}"
    )
