class FullNameValidatorMixin:
    @classmethod
    def validate_fullname(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Fullname should not be empty.")
        if not all(char.isalpha() or char.isspace() for char in value):
            raise ValueError("Fullname should contain only letters and space.")
        if len(value) >= 100:
            raise ValueError("Fullname should be less than 100 characters.")
        return value.title()
    
class PhoneNumberValidatorMixin:
    @classmethod
    def validate_phone_number(cls, phone_number: str) -> str:
        if not phone_number.isdigit():
            raise ValueError("Phone number must contain only digits.")
        if not (10 <= len(phone_number) <= 13):
            raise ValueError("Phone number must be between 10 to 13 digits long.")
        return phone_number