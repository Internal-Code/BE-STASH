import random
import string
from pydantic import EmailStr
from faker import Faker

faker = Faker()


async def random_number(length: int = 1) -> int:
    if length < 1:
        raise ValueError("length parameter should be more than 0")

    lower_bound = 10 ** (length - 1)
    upper_bound = 10**length - 1

    return random.randint(lower_bound, upper_bound)


async def random_word(length: int = 4) -> str:
    if length < 1:
        raise ValueError("length parameter should be more than 0")

    alphabet = string.ascii_lowercase
    word = "".join(random.choice(alphabet) for _ in range(length))

    return word


async def random_password(length: int = 8) -> str:
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    special = "".join(c for c in string.punctuation if c not in ['"', "'"])

    password = [
        random.choice(lower),
        random.choice(upper),
        random.choice(digits),
        random.choice(special),
    ]

    all_characters = lower + upper + digits + special
    password += random.choices(all_characters, k=length)

    random.shuffle(password)
    return "".join(password)


async def random_account(
    first_name: str = faker.first_name(),
    last_name: str = faker.last_name(),
    username: str = f"testing-{faker.first_name()}",
    email: EmailStr = faker.email(),
) -> dict:
    return {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "phone_number": await random_number(10),
        "password": await random_password(),
    }


async def generate_full_name(first_name: str, last_name: str) -> str:
    full_name = first_name + " " + last_name
    return full_name
