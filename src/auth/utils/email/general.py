from fastapi_mail import FastMail, MessageSchema, ConnectionConfig


async def mail_configuration() -> ConnectionConfig:
    configuration = ConnectionConfig(
        MAIL_USERNAME="no-reply",
        MAIL_PASSWORD="gbOQhR8swSBOg",
        MAIL_FROM="no-reply@financetracker.com",
        MAIL_PORT=1025,
        MAIL_SERVER="localhost",
        MAIL_SSL_TLS=False,
        MAIL_STARTTLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=False,
    )
    return configuration


async def send_email(subject: str, recipient: list, message: str) -> MessageSchema:
    messages = MessageSchema(
        subject=subject, recipients=recipient, body=message, subtype="html"
    )

    fast_mail = FastMail(await mail_configuration())
    return await fast_mail.send_message(message=messages)
