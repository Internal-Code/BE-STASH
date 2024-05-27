from api.database.databaseConnection import database_connection
from sqlalchemy.engine.base import Engine

def test_database_connetion() -> None:
    engine = database_connection()
    assert type(engine) == Engine