from datetime import datetime, timedelta
from gateway.database import db

rate_limit_collection = db["rate_limits"]

async def check_rate_limit(user_id: int, max_attempts: int = 3, window_minutes: int = 60) -> tuple[bool, int]:
    """Check if user exceeded rate limit. Returns (is_allowed, remaining_attempts)"""
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Get recent attempts
    user_data = await rate_limit_collection.find_one({"user_id": user_id})
    
    if not user_data:
        await rate_limit_collection.insert_one({
            "user_id": user_id,
            "attempts": [now],
            "last_attempt": now
        })
        return True, max_attempts - 1
    
    # Filter attempts within window
    recent_attempts = [a for a in user_data.get("attempts", []) if a > window_start]
    
    if len(recent_attempts) >= max_attempts:
        return False, 0
    
    # Add new attempt
    recent_attempts.append(now)
    await rate_limit_collection.update_one(
        {"user_id": user_id},
        {"$set": {"attempts": recent_attempts, "last_attempt": now}}
    )
    
    return True, max_attempts - len(recent_attempts)
