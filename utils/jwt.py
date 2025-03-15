from uuid import UUID
from fastapi import Depends
from datetime import timedelta
from jose import JWTError, jwt
from src.secret import Config
from utils.helper import local_time
from utils.logger import logging
from sqlalchemy.engine.row import Row
from typing import Annotated, Optional
from passlib.context import CryptContext
from utils.query import QueryDatabase
from fastapi.security import OAuth2PasswordBearer
from services.postgres.connection import get_db
from src.schema.validator import SecurityCodeValidator
from services.postgres.models import User, BlacklistToken
from utils.error import AuthenticationFailed, DataNotFoundError


class JWTHandler:
    def __init__(self):
        self.config = Config()
        self.password_content = CryptContext(schemes=["bcrypt"])

    def verify_pin(self, pin: str, hashed_pin: str) -> bool:
        return self.password_content.verify(pin, hashed_pin)

    def get_password_hash(self, password: str) -> str:
        return self.password_content.hash(password)

    async def authenticate_user(self, unique_id: UUID, pin: str) -> Optional[Row]:
        validated_pin = SecurityCodeValidator.validate_security_code(
            type="pin", value=pin
        )

        async for db in get_db():
            query = QueryDatabase(db)
            account_record = await query.find(table=User, unique_id=unique_id)

            if not account_record:
                raise DataNotFoundError(detail="User not found.")
            if not account_record.pin:
                raise AuthenticationFailed(detail="User has not set pin.")
            if not self.verify_pin(pin=validated_pin, hashed_pin=account_record.pin):
                raise AuthenticationFailed(detail="Invalid PIN.")

            return account_record

    def create_access_token(self, data: dict, access_token_expires: timedelta) -> str:
        to_encode = data.copy()
        expires = local_time() + access_token_expires
        to_encode.update({"exp": expires})
        encoded_access_token = jwt.encode(
            claims=to_encode, key=self.config.ACCESS_TOKEN_SECRET_KEY
        )

        return encoded_access_token

    def create_refresh_token(self, data: dict, refresh_token_expires: timedelta) -> str:
        to_encode = data.copy()
        expires = local_time() + refresh_token_expires
        to_encode.update({"exp": expires})
        encoded_refresh_token = jwt.encode(
            claims=to_encode, key=self.config.REFRESH_TOKEN_SECRET_KEY
        )
        return encoded_refresh_token

    async def get_current_user(
        self,
        token: Annotated[
            str, Depends(OAuth2PasswordBearer(tokenUrl="/user/general/login"))
        ],
    ) -> Optional[Row]:
        async for db in get_db():
            query = QueryDatabase(db)
            blacklisted_record = await query.find(
                table=BlacklistToken, access_token=token
            )

        try:
            if blacklisted_record:
                raise AuthenticationFailed(
                    detail="Session expired. Please perform re-login."
                )

            payload = jwt.decode(
                token=token,
                key=self.config.ACCESS_TOKEN_SECRET_KEY,
                algorithms=[self.config.ACCESS_TOKEN_ALGORITHM],
            )

            user_uuid = payload.get("sub")

            if not user_uuid:
                raise AuthenticationFailed(detail="Could not validate credentials.")

            async for db in get_db():
                query = QueryDatabase(db)
                users = await query.find(table=User, unique_id=user_uuid)

        except JWTError as e:
            logging.error(f"JWTError: {e}")
            raise AuthenticationFailed(detail="Invalid access token.")
        return users
