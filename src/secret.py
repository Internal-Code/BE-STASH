import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv

env_file = os.getenv("ENV_FILE")
if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
else:
    raise FileNotFoundError(f"Environment file not found: {env_file}")


POSTGRE_DATABASE = os.getenv("POSTGRE_DATABASE")
POSTGRE_USER = os.getenv("POSTGRE_USER")
POSTGRE_PASSWORD = os.getenv("POSTGRE_PASSWORD")
POSTGRE_HOST = os.getenv("POSTGRE_HOST")
POSTGRE_URL = f"postgresql+asyncpg://{POSTGRE_USER}:{POSTGRE_PASSWORD}@{POSTGRE_HOST}/{POSTGRE_DATABASE}"
ACCESS_TOKEN_EXPIRED = os.getenv("ACCESS_TOKEN_EXPIRED")
ACCESS_TOKEN_SECRET_KEY = os.getenv("ACCESS_TOKEN_SECRET_KEY")
REFRESH_TOKEN_EXPIRED = os.getenv("REFRESH_TOKEN_EXPIRED")
REFRESH_TOKEN_SECRET_KEY = os.getenv("REFRESH_TOKEN_SECRET_KEY")
MIDDLEWARE_SECRET_KEY = os.getenv("MIDDLEWARE_SECRET_KEY")
