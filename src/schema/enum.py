from enum import StrEnum, auto


class OtpRequestTypeEnum(StrEnum):
    reset_pin = auto()
    register_user = auto()
    verify_account = auto()
