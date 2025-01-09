from uuid import uuid4
from faker import Faker
from utils.generator import random_number

faker = Faker()
same_pin = random_number(length=6)

records_to_insert = [
    {"unique_id": str(uuid4()), "full_name": faker.name(), "phone_number": faker.phone_number(), "pin": same_pin},
    {"unique_id": str(uuid4()), "full_name": faker.name(), "phone_number": faker.phone_number(), "pin": same_pin},
    {
        "unique_id": str(uuid4()),
        "full_name": faker.name(),
        "phone_number": faker.phone_number(),
        "pin": random_number(length=6),
    },
]


fetched_data = {tuple(record.items()) for record in records_to_insert}
print(fetched_data)
