import pytest
import httpx
from jose import jwt
from datetime import datetime
from src.auth.utils.database.general import create_category_format
from src.auth.utils.generator import random_number, random_word
from src.secret import ACCESS_TOKEN_SECRET_KEY, ACCESS_TOKEN_ALGORITHM

TEST_USERNAME = "string"
TEST_PASSWORD = "String123!"


@pytest.mark.asyncio
async def test_create_schema_with_valid_token() -> None:
    """
    Should log in with valid credentials and create a new schema successfully.
    """
    async with httpx.AsyncClient() as client:
        login_data = {"username": TEST_USERNAME, "password": TEST_PASSWORD}

        token_response = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        assert token_response.status_code == 200

        tokens = token_response.json()
        access_token = tokens["access_token"]
        decoded_token = jwt.decode(
            access_token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM]
        )
        user_uuid = decoded_token["user_uuid"]

        data = create_category_format(
            user_uuid=user_uuid,
            month=random_number(),
            year=random_number(4),
            category=f"testing-{random_word()}",
            budget=random_number(10),
        )

        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        headers = {"Authorization": f"Bearer {access_token}"}

        schema_response = await client.post(
            "http://localhost:8000/api/v1/create-schema", json=data, headers=headers
        )
        assert schema_response.status_code == 201
