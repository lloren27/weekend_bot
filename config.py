import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

APP_NAME = os.getenv(
    "APP_NAME",
    "Weekend Bot",
)

TIMEZONE = "Europe/Madrid"

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)

CACHE_TTL_SECONDS = int(
    os.getenv(
        "CACHE_TTL_SECONDS",
        "1800",
    )
)
