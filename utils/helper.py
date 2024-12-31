from pytz import timezone
from datetime import datetime


def local_time(zone: str = "Asia/Jakarta") -> datetime:
    return datetime.now(timezone(zone))
