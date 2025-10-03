from enum import StrEnum, auto


class RoleNameEnum(StrEnum):
    admin = auto()
    user = auto()


class UserDeviceInfoEnum(StrEnum):
    android = auto()
    ios = auto()
    browser = auto()
    other = auto()


class UserGenderEnum(StrEnum):
    male = auto()
    female = auto()


class UserRegistrationStateEnum(StrEnum):
    pending = auto()
    completed = auto()


class SendOtpChannelEnum(StrEnum):
    whatsapp = auto()
    email = auto()


class TransactionPaymentMethodEnum(StrEnum):
    cash = auto()
    credit_card = auto()
    bank_transfer = auto()
    e_wallet = auto()


class ThirdPartyServiceTypeEnum(StrEnum):
    smtp = auto()
    local_whatsapp_api = auto()


class ThirdPartyServiceStatusEnum(StrEnum):
    success = auto()
    failed = auto()


class ErrorLogTypeEnum(StrEnum):
    known_error = auto()
    unknown_error = auto()
