import pytest
import httpx
from src.auth.utils.generator import random_number, random_word
from src.tests.auth.initialization import user_initialization

data = {
    "spend_day": random_number(),
    "spend_month": random_number(),
    "spend_year": random_number(4),
    "category": f"testing-category-{random_word(10)}",
    "description": f"testing-description{random_word(10)}",
    "amount": random_number(10),
}


@pytest.mark.asyncio
async def test_create_spends_with_valid_data(user_initialization) -> None:
    """
    Should create a new schema successfully.
    """
    async with httpx.AsyncClient() as client:
        account = await user_initialization

        login_data = {"username": account["username"], "password": account["password"]}

        token_response = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        print(token_response)
        assert token_response.status_code == 200

        tokens = token_response.json()
        access_token = tokens["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        schema_response = await client.post(
            "http://localhost:8000/api/v1/create-spend", json=data, headers=headers
        )
        print(schema_response.content)
        assert schema_response.status_code == 201
