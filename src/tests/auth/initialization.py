import pytest
import httpx
from src.auth.utils.generator import random_account


@pytest.fixture(scope="session")
async def user_initialization():
    async with httpx.AsyncClient() as client:
        account = random_account()
        res = await client.post("http://localhost:8000/api/v1/users/register", json=account)
        assert res.status_code == 201
        return account
