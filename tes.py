import asyncio
from services.postgres.connection import get_db
from services.postgres.models import User
from utils.query.general import insert_record


async def main():
    db = get_db()
    await insert_record(
        db=db,
        table=User,
        data={
            "unique_id": "sasddda",
            "full_name": "djaidai",
            "phone_number": "jdajadda",
            "email": "dicaadd@gm.com",
        },
    )


asyncio.run(main())
