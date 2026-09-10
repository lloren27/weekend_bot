from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import TIMEZONE


def get_next_weekend():
    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz).date()

    # Monday = 0 ... Friday = 4
    days_until_friday = (4 - today.weekday()) % 7

    friday = today + timedelta(days=days_until_friday)
    saturday = friday + timedelta(days=1)
    sunday = friday + timedelta(days=2)

    return friday, saturday, sunday