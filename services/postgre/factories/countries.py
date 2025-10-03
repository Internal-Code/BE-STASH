from faker import Faker
from services.postgre.query import DatabaseQuery
from sqlalchemy.ext.asyncio import AsyncSession
from factory.base import Factory
from typing import Any
from factory.declarations import Sequence, LazyFunction
from services.postgre.models import Countries
from utils.time import local_time

faker = Faker()


class CountriesFactory(Factory[Countries]):
    class Meta:
        model = Countries

    id = Sequence(lambda n: n + 1)
    created_at = LazyFunction(local_time)
    name = LazyFunction(lambda: faker.country())
    iso_code = LazyFunction(lambda: faker.country_code(representation="alpha-2"))
    dial_code = LazyFunction(lambda: faker.random_int(min=1, max=999))

    @classmethod
    async def create_country(cls, session: AsyncSession, **kwargs: dict[str, Any]) -> dict[str, Any]:
        db = DatabaseQuery(session)
        country_instance = cls.build(**kwargs)
        country_dict = country_instance.model_dump()
        await db.insert(Countries, country_dict)
        return country_dict
