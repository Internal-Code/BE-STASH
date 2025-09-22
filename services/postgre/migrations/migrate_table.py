import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from utils.logger import logging
from services.postgre.connection import drop_database, migrate_database, engine


async def main():
    try:
        await drop_database()
        await migrate_database()
    except Exception as e:
        logging.error(f"Table migration failed: {e}")
        sys.exit(1)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
