from dotenv import load_dotenv
import os

load_dotenv(override=True)

LOCAL_POSTGRESQL_USER = os.getenv("LOCAL_POSTGRESQL_USER")
LOCAL_POSTGRESQL_PASSWORD = os.getenv("LOCAL_POSTGRESQL_PASSWORD")
LOCAL_POSTGRESQL_HOST = os.getenv("LOCAL_POSTGRESQL_HOST")
LOCAL_POSTGRESQL_DATABASE = os.getenv("LOCAL_POSTGRESQL_DATABASE")
LOCAL_POSTGRESQL_POOL_SIZE = os.getenv("LOCAL_POSTGRESQL_POOL_SIZE")
LOCAL_POSTGRESQL_MAX_OVERFLOW = os.getenv("LOCAL_POSTGRESQL_MAX_OVERFLOW")
ACCESS_TOKEN_EXPIRED=os.getenv("ACCESS_TOKEN_EXPIRED")
ACCESS_TOKEN_ALGORITHM=os.getenv("ACCESS_TOKEN_ALGORITHM")
ACCESS_TOKEN_SECRET_KEY=os.getenv("ACCESS_TOKEN_SECRET_KEY")