import pytest
import httpx
from src.auth.utils.generator import random_word
from src.tests.auth.initialization import user_initialization

@pytest.mark.asyncio
async def test_login_with_random_credentials() -> None:
    """
    Should return invalid credentials.
    """

    login_data = {"username": random_word(10), "password": random_word(10)}

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_generate_new_access_token_with_valid_refresh_token(
    user_initialization,
) -> None:
    """
    Should generate new access_token using valid refresh token.
    """

    account = await user_initialization

    login_data = {"username": account["username"], "password": account["password"]}

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/auth/token", data=login_data
        )
        response = res.json()
        refresh_token = response["refresh_token"]

        refresh_token_res = await client.post(
            "http://localhost:8000/api/v1/auth/refresh-token",
            params={"refresh_token": refresh_token},
        )
        assert refresh_token_res.status_code == 200

@pytest.mark.asyncio
async def test_generate_new_access_token_with_invalid_refresh_token() -> None:
    """
    Should return 401 for invalid refresh token input params.
    """
    invalid_refresh_token = (
        "eyinvalidtokenheader.invalidtokenpayload.invalidtokensignature"
    )

    async with httpx.AsyncClient() as client:
        invalid_refresh_token_res = await client.post(
            "http://localhost:8000/api/v1/auth/refresh-token",
            params={"refresh_token": invalid_refresh_token},
        )
        assert invalid_refresh_token_res.status_code == 401
