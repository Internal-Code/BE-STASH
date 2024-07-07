import pytest
import httpx

@pytest.mark.asyncio
async def test_get_schema():
    """
    Should return list of category.
    """
    params = {
        "month": 6,
        "year": 9707
    }
    async with httpx.AsyncClient() as client:
        res = await client.request(
            method="GET",
            url="http://localhost:8000/api/v1/get_category",
            params=params
        )
        print(res)
        assert res.json().get('success') is True
        assert res.status_code == 200
        

@pytest.mark.asyncio        
async def test_validate_month():
    """
    Should return not found if category is parameter not found on table
    """
    params = {
        "month": 1,
        "year": 2024
    }
    async with httpx.AsyncClient() as client:
        res = await client.request(
            method="GET",
            url="http://localhost:8000/api/v1/get_category",
            params=params
        )
        assert res.status_code == 404

@pytest.mark.asyncio        
async def test_validate_month_not_found():
    """
    Should return forbidden if category is parameter not found on table
    """
    params = {
        "month": 60,
        "year": 2024
    }
    async with httpx.AsyncClient() as client:
        res = await client.request(
            method="GET",
            url="http://localhost:8000/api/v1/get_category",
            params=params
        )
        assert res.status_code == 403