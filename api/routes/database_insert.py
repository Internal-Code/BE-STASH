# from typing import Union
# from loguru import logger
# from datetime import datetime
# from fastapi import APIRouter, HTTPException
# from pytz import timezone
# from api.models.response import ResponseGeneral
# from api.supabase.supabase_conection import database_connection
# from api.supabase.supabase_model import spending_money

# router = APIRouter(tags=["crud"])
# database = database_connection()

# async def local_time(zone: str = "Asia/Jakarta") -> Union[datetime, None]:
#     try:
#         time = datetime.now(timezone(zone))
#     except Exception as E:
#         logger.error(f"Error while generating local time: {E}")
#         time = None
#     return time

# async def wrap_data(
#     category: str,
#     describe: str,
#     amount: float
# ) -> dict:
#     time = await local_time()
#     if not time:
#         raise HTTPException(status_code=500, detail="Could not generate local time")

#     data = {
#         "createdAt": time,
#         "category": category,
#         "describe": describe,
#         "amount": amount
#     }

#     return data

# async def insert_data(
#     category: str,
#     describe: str,
#     amount: float
# ):
#     logger.info("Endpoint Insert.")
    
#     # Prepare the data
#     data = await wrap_data(category, describe, amount)
    
#     # Insert data into the database
#     query = spending_money.insert().values(data)
#     try:
#         await database.execute(query)

#         return ResponseGeneral(status="success", message="Data inserted successfully")
#     except Exception as e:
#         logger.error(f"Error while inserting data: {e}")
#         raise HTTPException(status_code=500, detail="Data insertion failed")

# router.add_api_route(
#     methods=["POST"],
#     path="/api/v1/insert_data", 
#     response_model=ResponseGeneral,
#     endpoint=insert_data
# )