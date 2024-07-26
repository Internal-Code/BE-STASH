import httpx
import pytest
from faker import Faker
from src.auth.utils.generator import random_password, random_word

faker = Faker()

data = {
    "first_name": faker.first_name(),
    "last_name": faker.last_name(),
    "username": faker.user_name(),
    "email": faker.email(),
    "password": random_password(),
}


@pytest.mark.asyncio
async def test_create_user_with_valid_data() -> None:
    """
    Should register new users.
    """
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/users/register", json=data
        )
        assert res.status_code == 201


@pytest.mark.asyncio
async def test_create_user_with_username_is_already_saved() -> None:
    """
    Should return conflict due to username or email is already saved on db.
    """
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/users/register", json=data
        )
        assert res.status_code == 409


@pytest.mark.asyncio
async def test_create_user_with_invalid_email() -> None:
    """
    Should return unprocessable entity due invalid email format.
    """
    data = {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "username": faker.user_name(),
        "email": faker.first_name(),
        "password": random_password(),
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/users/register", json=data
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_user_with_weak_password() -> None:
    """
    Should return bad request due invalid weak password.
    """
    data = {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "username": faker.user_name(),
        "email": faker.email(),
        "password": random_word(10),
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/users/register", json=data
        )
        assert res.status_code == 400
