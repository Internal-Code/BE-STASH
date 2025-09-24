from errors.custom_error import InvalidInputError


class Validator:
    def phone_number(self, phone_number: str) -> str:
        if not phone_number:
            raise InvalidInputError("phone_number should not be empty.")
        if not phone_number.isdigit():
            raise InvalidInputError("phone_number must contain only digits.")
        if not (10 <= len(phone_number) <= 20):
            raise InvalidInputError(
                "phone_number must be between 10 to 20 digits long."
            )
        return phone_number

    def name(self, name: str) -> str:
        name = " ".join(name.split())
        if not name:
            raise InvalidInputError("Name should not be empty.")
        if not all(char.isalpha() for char in name):
            raise InvalidInputError("Name should contain only letters.")
        if len(name) >= 20:
            raise InvalidInputError("Name should be less than 20 characters.")
        return name.title()
