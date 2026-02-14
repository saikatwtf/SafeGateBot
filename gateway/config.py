import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "gateway_bot"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "827440611").split(",") if x]
