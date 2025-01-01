import asyncio
from utils.generator import random_number
from utils.query.general import update_entry
from services.postgres.models import User
from services.postgres.connection import get_db

generated_otp = str(random_number(6))
conditions = {
    "unique_id": "bd2cd1f0-81ec-4725-9a02-724d5bc6bac2",
}

updated_value = {"full_name": "YAHOO"}


async def main():
    async for db in get_db():  # Properly handle the async generator
        await update_entry(db=db, table=User, conditions=conditions, data=updated_value)


asyncio.run(main=main())
