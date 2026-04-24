import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI")
    DB_NAME: str = os.getenv("DB_NAME")

settings = Settings()

if not settings.MONGO_URI or not settings.DB_NAME:
    raise ImportError(
        f"Environment variables not loaded. Check if .env exists at {BASE_DIR}/.env"
    )

MESSAGE_CONTRIBUTION_LIMIT = 5
MESSAGE_CONTRIBUTION = 1
API_CODE = '460-476-132'
TRACKSCAPE_URL = 'https://bot.trackscape.app/api/chat/new-clan-chat'
ALLOWED_ROLE_ID = 831537437137829928
ETERNAL_GEM_MEMBER_ROLE = 1494702555832254555
RANKS = [{'name': 'Sapphire', 'id': 831537437137829928, 'requirement': 10}, {}]
GUILD_ID = 608022254227554401