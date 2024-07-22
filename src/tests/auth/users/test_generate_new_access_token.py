import pytest
import httpx
from jose import jwt
from src.secret import ACCESS_TOKEN_ALGORITHM, ACCESS_TOKEN_SECRET_KEY, REFRESH_TOKEN_SECRET_KEY

TEST_USERNAME = "string"
TEST_PASSWORD = "String123!"

@pytest.mark.asyncio
async def test_generate_new_access_token() -> None:
    """
    Should login with valid credentials.
    """
    
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/api/v1/auth/token", data=login_data)
        response = res.json()
        refresh_token = response['refresh_token']
        assert res.status_code == 200
        
        """
        Should generate new access_token using valid refresh token.
        """
        refresh_token_res = await client.post("http://localhost:8000/api/v1/auth/refresh-token", params=f'refresh_token={refresh_token}')
        assert refresh_token_res.status_code == 200        

        """
        Should return 401 for invalid refresh token input params
        """
        invalid_refresh_token_res = await client.post("http://localhost:8000/api/v1/auth/refresh-token", params='refresh_token=invalidtoken')
        assert invalid_refresh_token_res.status_code == 401
        await client.aclose()