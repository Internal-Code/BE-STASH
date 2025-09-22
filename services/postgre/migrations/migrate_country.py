import sys
import os
import json
import asyncio
from pathlib import Path
from typing import cast, List, Any

sys.path.append(str(Path(__file__).resolve().parents[3]))
from utils.logger import logging
from services.postgre.connection import engine, async_session
from services.postgre.factories import CountriesFactory
from helpers.formatter import CustomFormatter

PROJECT_DIR = Path(__file__).resolve().parents[3]
JSON_PATH = "json/countries.json"
FILE_PATH = os.path.join(PROJECT_DIR, JSON_PATH)
FORMATTER = CustomFormatter()


async def main():
    logging.info("Starting countries data initialization.")
    if not os.path.exists(FILE_PATH):
        logging.error(f"File not found: {FILE_PATH}")
        sys.exit(1)

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        countries = json.load(f)
        countries = cast(List[dict[str, Any]], FORMATTER.to_int(countries, "dial_code"))

    async with async_session() as session:
        try:
            for country in countries:
                await CountriesFactory.create_country(session, **country)

            await session.commit()
            logging.info(f"Inserted {len(countries)} countries successfully.")

        except Exception as e:
            logging.error(f"Failed to insert country data. Error: {e}")
            await session.rollback()
            sys.exit(1)
        finally:
            await engine.dispose()
    logging.info("Countries data initialization completed.")


asyncio.run(main())
