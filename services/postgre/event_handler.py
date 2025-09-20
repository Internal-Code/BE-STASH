import os
from services.postgre.connection import get_db
from services.postgre.models.countries import Countries
from utils.query import QueryDatabase
from pathlib import Path
from utils.logger import logging
from utils.helper import load_json

PROJECT_DIR = Path(__file__).resolve().parents[2]
COUNTRIES_PATH = os.path.join(PROJECT_DIR, "json/countries.json")
COUNTRIES_DATA = load_json(COUNTRIES_PATH)


async def migrate_country():
    async for session in get_db():
        db = QueryDatabase(session=session)
        try:
            entry = await db.find(Countries, id=1)
            if entry:
                logging.info("Skipping re-entry. Country data already exists.")
            else:
                for country in COUNTRIES_DATA:
                    await db.insert(Countries, country)
        except Exception as e:
            logging.error(f"Failed to insert record: {e}")
            raise Exception(e)
