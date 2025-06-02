from enum import StrEnum, auto

class Environment(StrEnum):
    TEST = auto()
    DEV = auto()
    STAGING = auto()
    PRODUCTION = auto()

class DeviceInfo(StrEnum):
    ANDROID = auto()
    IOS = auto()
    OTHER = auto()

class Channel(StrEnum):
    WHATSAPP = auto()
    EMAIL = auto()

class PaymentType(StrEnum):
    CASH = auto()
    CREDIT_CARD = auto()
    BANK_TRANSFER = auto()
    E_WALLET = auto()
