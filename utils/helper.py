from pytz import timezone
from datetime import datetime


def local_time(zone: str = "Asia/Jakarta") -> datetime:
    return datetime.now(timezone(zone)).replace(tzinfo=None)


def leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False
