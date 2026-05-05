import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI")
    DB_NAME: str = os.getenv("DB_NAME")
    API_CODE: str = os.getenv("API_CODE")

settings = Settings()

if not settings.MONGO_URI or not settings.DB_NAME:
    raise ImportError(
        f"Environment variables not loaded. Check if .env exists at {BASE_DIR}/.env"
    )

MESSAGE_CONTRIBUTION_LIMIT = 5
MESSAGE_CONTRIBUTION = 1
TRACKSCAPE_URL = 'https://bot.trackscape.app/api/chat/new-clan-chat'
ALLOWED_ROLE_ID = [831537437137829928]
ETERNAL_GEM_MEMBER_ROLE = 1497637732804202607
RANKS = [{'name': 'Opal', 'id': 1497641590213050440, 'requirement': 0},
         {'name': 'Sapphire', 'id': 1497640713851240498, 'requirement': 10}]
GUILD_ID = 1462934610496196863
STAFF_ROLES = [1462937098184298801]