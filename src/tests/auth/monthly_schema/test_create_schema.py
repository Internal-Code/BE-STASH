import pytest
import httpx
from src.database.models import money_spend_schema
from src.database.connection import database_connection
from sqlalchemy import select

@pytest.fixture(scope="session")
def db_data():
    with database_connection().connect() as session:
        with session.begin():
            res = session.execute(select(money_spend_schema))
            col = res.keys()
            rows = res.fetchall()
            result = []

            for row in rows:
                row_dict = {col: getattr(row, col) for col in col}
                result.append(row_dict)

        session.close()
    return result

# @pytest.mark.asyncio    
# async def test_insert_create_schema(db_data):
#     """
#     Should create schema into table.
#     """
#     sample_data = db_data[0]
#     async with httpx.AsyncClient() as client:
#         res = await client.post("http://localhost:8000/api/v1/create_schema", json=sample_data[0])
#         assert res.json().get('success') == True
#         assert res.status_code == 201
#         await client.aclose()
        
@pytest.mark.asyncio
async def test_validate_create_schema(db_data):
    """
    Should return forbidden if any same schema inside the table.
    """
    sample_data = db_data[0]
    print(sample_data)
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/api/v1/create_schema", json=sample_data)
        assert res.status_code == 403
        await client.aclose()