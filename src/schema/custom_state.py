from enum import auto, StrEnum


class SendLinkMethod(StrEnum):
    PHONE_NUMBER = auto()
    EMAIL = auto()


class RegisterAccountState(StrEnum):
    ON_PROCESS = auto()
    SUCCESS = auto()
