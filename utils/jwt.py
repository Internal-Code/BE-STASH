import json
from uuid import UUID
from typing import Optional, Any, cast, Literal
from datetime import timedelta, datetime
from errors.custom_error import (
    AuthenticationError,
    NotFoundError,
    MandatoryInputError,
    BaseError,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import aliased
from sqlalchemy import ColumnElement, func
from cryptography.fernet import Fernet
from utils.time import local_time
from utils.logger import logging
from services.postgre.connection import async_session
from services.postgre.models import Users, BlacklistedTokens, Countries, UserTokens
from services.postgre.query import DatabaseQuery
from services.postgre.query_schema import SelectData, Filters
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from src.secret import (
    ACCESS_TOKEN_JWT_EXPIRED,
    ACCESS_TOKEN_JWT_SECRET_KEY,
    REFRESH_TOKEN_JWT_EXPIRED,
    ACCESS_TOKEN_FERNET_SECRET_KEY,
)
from src.schema.validator import Validator

validator = Validator()


class JWTConfig:
    def __init__(self):
        self.password_content = CryptContext(schemes=["bcrypt"])
        self.fernet = Fernet(key=ACCESS_TOKEN_FERNET_SECRET_KEY)
        self.u = aliased(Users)
        self.bt = aliased(BlacklistedTokens)
        self.c = aliased(Countries)
        self.ut = aliased(UserTokens)

    def to_verify(self, pin: str, hashed_pin: str) -> bool:
        validated_pin = validator.number(data=pin, exact_length=6)
        validated_pin = self.password_content.verify(
            secret=validated_pin, hash=hashed_pin
        )
        return validated_pin

    def to_hashed(self, pin: str) -> str:
        validated_pin = validator.number(data=pin, exact_length=6)
        hashed_pin = self.password_content.hash(secret=validated_pin)
        return hashed_pin

    async def auth_user(self, user_uid: UUID, pin: str) -> Optional[dict[str, Any]]:
        logging.info("Authenticating user...", extra={"user_uid": str(user_uid)})
        validated_pin = validator.number(data=pin, exact_length=6)
        async with async_session() as session:
            db = DatabaseQuery(session=session)
            u_select = SelectData(
                entry=[
                    cast(ColumnElement[Any], self.u.id).label("id"),
                    cast(ColumnElement[Any], self.u.uid).label("uid"),
                    cast(ColumnElement[Any], self.u.name).label("name"),
                    cast(ColumnElement[Any], self.u.email).label("email"),
                    func.concat(self.c.dial_code, self.u.phone_number).label(
                        "phone_numbear"
                    ),
                    cast(ColumnElement[Any], self.u.gender).label("gender"),
                ]
            )
            u_join = SelectData(entry=[[self.c, self.c.id == self.u.country_id]])
            u_filter = Filters(
                filters=[
                    Filters(
                        field_name=self.u.uid, filter_type="equal", value=str(user_uid)
                    )
                ]
            )
            user_data: Any = await db.fetch(
                field_names=u_select,
                master_table=self.u,
                join_tables=u_join,
                filters=u_filter,
                fetch_type="one",
            )

            if not user_data:
                logging.warning(
                    "User not found during authentication.",
                    extra={"user_uid": str(user_uid)},
                )
                raise NotFoundError(f"User {user_uid} not found.")

            username = user_data["name"]

            if not user_data["pin"]:
                logging.warning(
                    "User has no PIN set.",
                    extra={"user_uid": str(user_uid), "username": username},
                )
                raise MandatoryInputError(f"User {username} has not set up a PIN yet.")

            verified_pin = self.to_verify(
                pin=validated_pin, hashed_pin=user_data["pin"]
            )
            if not verified_pin:
                logging.warning(
                    "Invalid PIN attempt.",
                    extra={"user_uid": str(user_uid), "username": username},
                )
                raise AuthenticationError("Invalid pin.")

            logging.info(
                "User authenticated successfully.", extra={"user_uid": str(user_uid)}
            )
            return user_data

        return None

    def create_token(
        self, data: dict[str, Any], token_type: Literal["access", "refresh"]
    ) -> str:
        # Decide expiration based on token type
        match token_type:
            case "access":
                expire_at = local_time() + timedelta(
                    minutes=int(ACCESS_TOKEN_JWT_EXPIRED)
                )
            case "refresh":
                expire_at = local_time() + timedelta(
                    minutes=int(REFRESH_TOKEN_JWT_EXPIRED)
                )
            case _:
                raise ValueError(f"Unsupported token_type: {token_type}")

        # Add expiration claim
        data.update({"exp": expire_at.isoformat()})

        # Encrypt payload
        payload = json.dumps(data).encode()
        encrypted_payload = self.fernet.encrypt(payload).decode()

        # Build JWT payload
        jwt_payload: dict[str, Any] = {"encrypted": encrypted_payload, "exp": expire_at}
        token = jwt.encode(claims=jwt_payload, key=ACCESS_TOKEN_JWT_SECRET_KEY)

        logging.info(
            f"{token_type.capitalize()} token created successfully.",
            extra={
                "user_uid": str(data.get("uid")),
                "expires_at": expire_at.isoformat(),
                "token_type": token_type,
                "claims_keys": list(data.keys()),
            },
        )

        return token

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            # Decode JWT first
            decoded_jwt = jwt.decode(token=token, key=ACCESS_TOKEN_JWT_SECRET_KEY)
            encrypted_data = decoded_jwt["encrypted"]
            if not encrypted_data:
                logging.error(
                    "Token missing 'encrypted' field.",
                    extra={"token": token[:10] + "..."},
                )
                raise NotFoundError(
                    "Missing encrypted key.", {"encrypted": "Key not found"}
                )

            # Decrypt payload
            try:
                decrypted = self.fernet.decrypt(encrypted_data.encode())
            except Exception as exc:
                logging.error(
                    "Token decryption failed.", extra={"token": token[:10] + "..."}
                )
                raise AuthenticationError(
                    "Invalid token.", {"token": "Decryption failed.", "error": exc}
                )

            # Parse decrypted JSON
            try:
                data = json.loads(decrypted.decode())
            except json.JSONDecodeError as je:
                logging.error(
                    "Decrypted payload is not valid JSON.",
                    extra={"decrypted": decrypted[:50]},
                )
                raise AuthenticationError(
                    "Invalid token payload.", {"payload": "Invalid JSON", "error": je}
                )

            # Expiration check
            exp = data.get("exp")
            if exp and datetime.fromisoformat(exp) < local_time():
                logging.warning("Expired token used.", extra={"exp": exp})
                raise AuthenticationError("Token expired.", {"exp": exp})

            logging.info(
                "Token decoded successfully.",
                extra={"uid": data.get("uid"), "exp": exp},
            )

        except BaseError:
            raise
        except Exception as e:
            logging.error("Unexpected error decoding token.", exc_info=True)
            raise AuthenticationError("Invalid token.", {"token": str(e)})
        return data

    async def get_user(
        self,
        token: str = Depends(
            OAuth2PasswordBearer(tokenUrl="/api/v1/auth/access-token")
        ),
    ) -> dict[str, Any]:
        try:
            payload = self.decode_token(token)
            user_id = payload["uid"]

            if not user_id:
                raise NotFoundError("Data not found", {"user_id": "User not found."})

            # Open DB session context
            async with async_session() as session:
                db = DatabaseQuery(session=session)

                # Check if token is registered
                ut_filter = Filters(
                    filter_type="equal",
                    field_name=self.ut.access_token,
                    value=token,
                )

                user_token = await db.fetch(
                    master_table=self.ut, filters=ut_filter, fetch_type="one"
                )

                if not user_token:
                    raise AuthenticationError(
                        "Session expired",
                        {"token": "Session expired. Please re-generate access token."},
                    )

                # Prepare user join with Employees & PositionBackups
                u_select = SelectData(
                    entry=[
                        cast(ColumnElement[Any], self.u.id).label("id"),
                        cast(ColumnElement[Any], self.u.uid).label("uid"),
                        cast(ColumnElement[Any], self.u.name).label("name"),
                        cast(ColumnElement[Any], self.u.email).label("email"),
                        func.concat(self.c.dial_code, self.u.phone_number).label(
                            "phone_numbear"
                        ),
                        cast(ColumnElement[Any], self.u.gender).label("gender"),
                    ]
                )
                u_join = SelectData(entry=[[self.c, self.c.id == self.u.country_id]])
                u_filter = Filters(
                    filters=[
                        Filters(
                            field_name=self.u.uid,
                            filter_type="equal",
                            value=str(user_id),
                        )
                    ]
                )
                user_data: Any = await db.fetch(
                    field_names=u_select,
                    master_table=self.u,
                    join_tables=u_join,
                    filters=u_filter,
                    fetch_type="one",
                )

                if not user_data:
                    raise NotFoundError("User not found", {"user_id": str(user_id)})

        except JWTError as je:
            raise AuthenticationError("Invalid access token.", {"errors": str(je)})

        return user_data
