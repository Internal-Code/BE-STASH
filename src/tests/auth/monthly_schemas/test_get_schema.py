import pytest
import httpx
from src.auth.utils.database.general import local_time
from src.auth.utils.generator import random_number, random_word
from src.tests.auth.initialization import user_initialization

login_data = {"username": "string", "password": "String123!"}

@pytest.mark.asyncio
async def test_list_category_with_valid_token_no_params(user_initialization) -> None:
    """
    Should return the latest schema for the current user without any parameters.
    """

    async with httpx.AsyncClient() as client:
        account = await user_initialization

        login_data = {"username": account["username"], "password": account["password"]}

        res = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        response = res.json()
        access_token = response["access_token"]
        assert res.status_code == 200

        headers = {"Authorization": f"Bearer {access_token}"}

        get_data = await client.get(
            "http://localhost:8000/api/v1/list-category", headers=headers
        )
        assert get_data.status_code == 200


@pytest.mark.asyncio
async def test_list_category_with_valid_token_and_params() -> None:
    """
    Should return the latest schema for the current user with given month and year parameters.
    """

    async with httpx.AsyncClient() as client:

        res = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        response = res.json()
        access_token = response["access_token"]
        assert res.status_code == 200

        headers = {"Authorization": f"Bearer {access_token}"}

        current_month = local_time().month
        current_year = local_time().year

        get_data = await client.get(
            "http://localhost:8000/api/v1/list-category",
            headers=headers,
            params={"month": current_month, "year": current_year},
        )
        assert get_data.status_code == 200


@pytest.mark.asyncio
async def test_list_category_with_invalid_token() -> None:
    """
    Should return 401 for requests with invalid bearer token.
    """

    async with httpx.AsyncClient() as client:
        access_token = f"{random_word(10)}.{random_word(10)}.{random_word(10)}"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        get_data = await client.get(
            "http://localhost:8000/api/v1/list-category", headers=headers
        )
        assert get_data.status_code == 401


@pytest.mark.asyncio
async def test_list_category_with_valid_token_and_nonexistent_params() -> None:
    """
    Should return 404 when querying with parameters not available in the database.
    """

    async with httpx.AsyncClient() as client:

        res = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        response = res.json()
        access_token = response["access_token"]
        assert res.status_code == 200

        headers = {"Authorization": f"Bearer {access_token}"}

        random_month = random_number()
        random_year = random_number(4)

        get_data = await client.get(
            "http://localhost:8000/api/v1/list-category",
            headers=headers,
            params={"month": random_month, "year": random_year},
        )
        assert get_data.status_code == 404