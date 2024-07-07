import pytest
import httpx
from src.utils.generator import random_word, random_number

base_json = {
        "month": 9,
        "year": 3892,
        "category": "fumwhjifey",
        "changed_category_into": "sjdijdsa"
    }

@pytest.mark.asyncio
async def test_update_schema():
    """
    Should updated category.
    """
    async with httpx.AsyncClient() as client:
        res = await client.patch("http://localhost:8000/api/v1/update_category", json=base_json)
        assert res.json().get('success') == True
        assert res.status_code == 200
        await client.aclose()
        
@pytest.mark.asyncio
async def test_validate_update_schema():
    """
    Should return forbidden if any same schema already inside the table.
    """
    sample_data = {
        "month": 5,
        "year": 2024,
        "category": base_json['changed_category_into'],
        "changed_category_into": base_json['changed_category_into']
    }
    async with httpx.AsyncClient() as client:
        res = await client.patch("http://localhost:8000/api/v1/update_category", json=sample_data)
        assert res.status_code == 403
        await client.aclose()

@pytest.mark.asyncio        
async def test_validate_category():
    """
    Should return not found if month, year, category is not found on table
    """
    sample_data = {
        "month": random_number(),
        "year": random_number(),
        "category": random_word(),
        "changed_category_into": random_word()
    }
    async with httpx.AsyncClient() as client:
        res = await client.patch("http://localhost:8000/api/v1/update_category", json=sample_data)
        assert res.status_code == 404
        await client.aclose()