import pytest
import httpx
from src.auth.utils.generator import random_word

@pytest.mark.asyncio
async def test_delete_schema():
    """
    Should delete category.
    """
    sample_data = {
        "month": 8,
        "year": 3928,
        "category": "kegmjwzott"
    }
    async with httpx.AsyncClient() as client:
        res = await client.request(
            method="DELETE",
            url="http://localhost:8000/api/v1/delete_category",
            json=sample_data
        )
        assert res.json().get('success') is True
        assert res.status_code == 200
        

@pytest.mark.asyncio        
async def test_validate_category():
    """
    Should return not found if category is not found on table
    """
    sample_data = {
        "month": 6,
        "year": 2024,
        "category": random_word()
    }
    async with httpx.AsyncClient() as client:
        res = await client.request(
            method="DELETE",
            url="http://localhost:8000/api/v1/delete_category",
            json=sample_data
        )
        assert res.status_code == 404
