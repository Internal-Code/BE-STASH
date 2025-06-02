import json
from pathlib import Path
from utils.logger import logging
from pytz import timezone
from datetime import datetime


def local_time(zone: str = "Asia/Jakarta") -> datetime:
    return datetime.now(timezone(zone)).replace(tzinfo=None)


def load_json(filepath: str) -> dict:
    logging.info(f"Loading JSON data from {filepath}.")
    return json.loads(Path(filepath).read_text())
