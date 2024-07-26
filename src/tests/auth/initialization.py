import pytest
import httpx
from faker import Faker
from src.auth.utils.generator import random_account

faker = Faker()

@pytest.fixture(scope="session")
async def user_initialization():
    """
    Initialize register account for unit tetsing purpose

    Returns:
        dict: should return account string.
    """
    async with httpx.AsyncClient() as client:
        account = random_account(
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            username="string",
            password="String123!",
            email=faker.email()
        )
        res = await client.post(
            "http://localhost:8000/api/v1/users/register", json=account
        )

        if res.status_code == 409:

            login_data = {
                "username": "string",
                "password": "String123!"
            }
            login_res = await client.post(
                "http://localhost:8000/api/v1/auth/token", data=login_data
            )

            assert login_res.status_code == 200
            return login_data

        assert res.status_code == 201
        return account
