# import pytest
# import httpx
# from datetime import datetime
# from utils.database.general import local_time
# from utils.generator import random_number, random_word
# from src.tests.auth.initialization import user_initialization

# data = {
#         "created_at": local_time(),
#         "updated_at": None,
#         "user_uuid": None,
#         "month": local_time().month,
#         "year": local_time().year,
#         "category": f"testing-{random_word(10)}",
#         "budget": random_number(10),
#         }


# @pytest.mark.asyncio
# async def test_create_schema_with_valid_data(user_initialization) -> None:
#     """
#     Should create a new schema successfully.
#     """
#     async with httpx.AsyncClient() as client:
#         account = await user_initialization

#         login_data = {"username": account["username"], "password": account["password"]}

#         token_response = await client.post(
#             "http://localhost:8000/api/v1/auth/token", data=login_data
#         )
#         assert token_response.status_code == 200

#         tokens = token_response.json()
#         access_token = tokens["access_token"]

#         for key, value in data.items():
#             if isinstance(value, datetime):
#                 data[key] = value.isoformat()

#         headers = {"Authorization": f"Bearer {access_token}"}

#         schema_response = await client.post(
#             "http://localhost:8000/api/v1/create-schema", json=data, headers=headers
#         )
#         assert schema_response.status_code == 201

# @pytest.mark.asyncio
# async def test_create_schema_with_category_already_saved(user_initialization) -> None:
#     """
#     Should return forbidden due to same category on database.
#     """
#     async with httpx.AsyncClient() as client:
#         account = await user_initialization

#         login_data = {"username": account["username"], "password": account["password"]}

#         token_response = await client.post(
#             "http://localhost:8000/api/v1/auth/token", data=login_data
#         )
#         assert token_response.status_code == 200

#         tokens = token_response.json()
#         access_token = tokens["access_token"]

#         for key, value in data.items():
#             if isinstance(value, datetime):
#                 data[key] = value.isoformat()

#         headers = {"Authorization": f"Bearer {access_token}"}

#         schema_response = await client.post(
#             "http://localhost:8000/api/v1/create-schema", json=data, headers=headers
#         )
#         assert schema_response.status_code == 403

# @pytest.mark.asyncio
# async def test_create_schema_with_invalid_token() -> None:
#     """
#     Should return forbidden due to invalid access token.
#     """
#     async with httpx.AsyncClient() as client:

#         access_token = f"{random_word(10)}.{random_word(10)}.{random_word(10)}"
#         data = {
#                 "created_at": local_time(),
#                 "updated_at": None,
#                 "user_uuid": None,
#                 "month": random_number(),
#                 "year": random_number(4),
#                 "category": f"testing-{random_word(10)}",
#                 "budget": random_number(10),
#                 }

#         for key, value in data.items():
#             if isinstance(value, datetime):
#                 data[key] = value.isoformat()

#         headers = {"Authorization": f"Bearer {access_token}"}

#         schema_response = await client.post(
#             "http://localhost:8000/api/v1/create-schema", json=data, headers=headers
#         )
#         assert schema_response.status_code == 401

# @pytest.mark.asyncio
# async def test_create_schema_with_invalid_format_data(user_initialization) -> None:
#     """
#     Should return unprocessable entity due to invalid payload.
#     """
#     async with httpx.AsyncClient() as client:
#         account = await user_initialization

#         login_data = {"username": account["username"], "password": account["password"]}

#         token_response = await client.post(
#             "http://localhost:8000/api/v1/auth/token", data=login_data
#         )
#         assert token_response.status_code == 200

#         tokens = token_response.json()
#         access_token = tokens["access_token"]

#         data = {
#                 "month": random_number(),
#                 "year": random_number(),
#                 "category": f"testing-{random_word(10)}",
#                 "budget": random_number(10),
#                 }


#         headers = {"Authorization": f"Bearer {access_token}"}

#         schema_response = await client.post(
#             "http://localhost:8000/api/v1/create-schema", json=data, headers=headers
#         )

#         assert schema_response.status_code == 422
