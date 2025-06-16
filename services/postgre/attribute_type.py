from enum import StrEnum, auto


class Environment(StrEnum):
    test = auto()
    dev = auto()
    staging = auto()
    production = auto()


class DeviceInfo(StrEnum):
    android = auto()
    ios = auto()
    other = auto()


class Channel(StrEnum):
    whatsapp = auto()
    email = auto()


class PaymentType(StrEnum):
    cash = auto()
    credit_card = auto()
    bank_transfer = auto()
    e_wallet = auto()
