import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv

env_file = os.getenv("ENV_FILE_PATH", "env/.env.development")
if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
else:
    raise FileNotFoundError(f"Environment file not found: {env_file}")


class Config:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_VERSION = os.getenv("POSTGRES_VERSION")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
    PGADMIN_VERSION = os.getenv("PGADMIN_VERSION")
    PGADMIN_EMAIL = os.getenv("PGADMIN_EMAIL")
    PGADMIN_PASSWORD = os.getenv("PGADMIN_PASSWORD")
    WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION")
    WHATSAPP_API_CONNECTION = os.getenv("WHATSAPP_API_CONNECTION")
    WHATSAPP_API_SECRET_SESSION = os.getenv("WHATSAPP_API_SECRET_SESSION")
    WHATSAPP_API_MESSAGE = os.getenv("WHATSAPP_API_MESSAGE")
    ACCESS_TOKEN_EXPIRED = os.getenv("ACCESS_TOKEN_EXPIRED")
    ACCESS_TOKEN_SECRET_KEY = os.getenv("ACCESS_TOKEN_SECRET_KEY")
    ACCESS_TOKEN_ALGORITHM = os.getenv("ACCESS_TOKEN_ALGORITHM")
    REFRESH_TOKEN_EXPIRED = os.getenv("REFRESH_TOKEN_EXPIRED")
    REFRESH_TOKEN_SECRET_KEY = os.getenv("REFRESH_TOKEN_SECRET_KEY")
    MIDDLEWARE_SECRET_KEY = os.getenv("MIDDLEWARE_SECRET_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_APP_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")
    GOOGLE_DEFAULT_EMAIL = os.getenv("GOOGLE_DEFAULT_EMAIL")
    GOOGLE_SMTP_SERVER = os.getenv("GOOGLE_SMTP_SERVER")
    GOOGLE_SMTP_PORT = os.getenv("GOOGLE_SMTP_PORT")
