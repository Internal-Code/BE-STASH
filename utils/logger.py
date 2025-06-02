import os
import logging
from pathlib import Path

BASE_FORMAT = "%(asctime)s %(levelname)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
BASE_PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_TYPE = os.getenv("ENV_TYPE", "dev")
LOG_DIR = BASE_PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"server-{ENV_TYPE}.log"

logging.basicConfig(
    level=logging.INFO,
    format=BASE_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a"),
    ],
)
