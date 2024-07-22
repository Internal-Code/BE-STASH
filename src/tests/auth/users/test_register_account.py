import httpx, pytest
from faker import Faker
from src.auth.utils.generator import random_password

faker = Faker()

@pytest.mark.asyncio
async def test_create_user() -> None:
    """
    Should register new users
    """
    data = {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "username": faker.user_name(),
        "email": faker.email(),
        "password": random_password()
    }
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/api/v1/users/register", json=data)
        assert res.status_code == 201