from typing import Literal


class Validator:
    def phone_number(self, phone_number: str) -> str:
        if not phone_number:
            raise ValueError("phone_number should not be empty.")
        if not phone_number.isdigit():
            raise ValueError("phone_number must contain only digits.")
        if not (10 <= len(phone_number) <= 20):
            raise ValueError("phone_number must be between 10 to 20 digits long.")
        return phone_number

    def name(self, name: str, field: Literal["first_name", "last_name"]) -> str:
        name = " ".join(name.split())
        if not name:
            raise ValueError(f"{field} should not be empty.")
        if not all(char.isalpha() for char in name):
            raise ValueError(f"{field} should contain only letters.")
        if len(name) >= 20:
            raise ValueError(f"{field} should be less than 20 characters.")
        return name.title()
