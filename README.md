# Gateway-Bot (SafeGateBot)

![SafeGateBot Banner](https://i.ibb.co/xtQRypjh/x.jpg)

A Telegram bot that manages access to private channels using deep linking, captcha verification, and single-use invite links.

🤖 **Active Bot:** https://t.me/SafeGateBot  
📦 **Repository:** https://github.com/saikatwtf/SafeGateBot

---

## Features
- Deep linking with unique short codes
- Captcha verification before access
- Dynamic single-use invite links (expires in 10 minutes)
- MongoDB database for channel mapping
- Public bot - anyone can add their channels
- Multi-channel support per user with button interface
- Auto-add when bot is promoted to admin
- Add channels by forwarding messages
- Channel statistics tracking (attempts, joins, success rate)
- Rate limiting (3 captcha attempts per hour)
- Delete channels via button interface
- Auto-accept join requests (toggle per channel)
- Broadcast messages to all users (admin only)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. MongoDB Setup
Install MongoDB locally or use MongoDB Atlas (cloud):
- Local: https://www.mongodb.com/try/download/community
- Atlas: https://www.mongodb.com/cloud/atlas

### 3. Configure Environment
Copy `.env.example` to `.env` and fill in:
```
BOT_TOKEN=your_bot_token_from_botfather
MONGO_URI=mongodb://localhost:27017
ADMIN_IDS=your_telegram_user_id
```

### 4. Make Bot Admin
Add the bot to your target channel/group and promote it to admin with "Invite Users" permission.

### 5. Run
```bash
python -m gateway
```
Or use the run script:
```bash
python run.py
```

## Usage

### User Commands
- `/addchannel <channel_id>` - Add your channel manually
  - Example: `/addchannel -1001234567890`
  - Bot must be admin in the channel
- **Auto-add**: Make bot admin in your channel (automatically adds it)
- **Forward method**: Forward any message from your channel to the bot
- `/mychannels` - View all your channels with clickable deep links

### Access Flow
1. User clicks deep link (e.g., `https://t.me/YourBot?start=au26edd`)
2. Bot sends captcha image
3. User solves captcha: `/join <code>`
4. Bot generates single-use invite link valid for 10 minutes
5. User joins channel

## Security
- Actual channel links never exposed
- Single-use invite links (member_limit=1)
- Time-limited access (10 minutes)
- Captcha prevents automated abuse
- Each user manages their own channels
