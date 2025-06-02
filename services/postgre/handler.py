import os
import asyncio
from services.postgre.connection import get_db
from services.postgre.model import Country
from utils.query import QueryDatabase
from pathlib import Path
from utils.logger import logging
from utils.helper import load_json

BASE_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
JSON_FILE = os.path.join(BASE_PROJECT_DIR, "json/countries.json")

data = load_json(filepath=JSON_FILE)

async def migrate_country():
    async for session in get_db():
        db = QueryDatabase(session=session)
        try:
            entry = await db.find(Country, id=1)
            if entry:
                logging.info("Skipping re-entry. Country data already inserted.")
            else:
                for entry in data:
                    await db.insert(Country, entry)
        except Exception as e:
            logging.error(f'Failed to insert record: {e}')
            raise Exception(e)