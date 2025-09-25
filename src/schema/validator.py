from errors.custom_error import InvalidInputError


class Validator:
    def number(
        self,
        data: str,
        min_length: int = 1,
        max_length: int = 20,
        allow_leading_zero: bool = True,
        exact_length: int | None = None,
    ) -> str:
        if not data or not data.strip():
            raise InvalidInputError("Number should not be empty.")

        # Strict digit check
        if not data.isdigit():
            raise InvalidInputError("Number must contain only digits.")

        # Exact length check (e.g., OTP codes)
        if exact_length is not None and len(data) != exact_length:
            raise InvalidInputError(f"Number must be exactly {exact_length} digits.")

        # General min/max length check
        if not (min_length <= len(data) <= max_length):
            raise InvalidInputError(
                f"Number must be between {min_length} and {max_length} digits."
            )

        # Leading zero check (e.g., for some IDs, not for phone numbers)
        if not allow_leading_zero and data.startswith("0"):
            raise InvalidInputError("Number must not start with zero.")

        return data

    def name(self, name: str) -> str:
        name = " ".join(name.split())
        if not name:
            raise InvalidInputError("Name should not be empty.")
        if not all(char.isalpha() for char in name):
            raise InvalidInputError("Name should contain only letters.")
        if len(name) >= 20:
            raise InvalidInputError("Name should be less than 20 characters.")
        return name.title()
