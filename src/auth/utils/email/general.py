from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import smtplib
import ssl
from pydantic import EmailStr
from src.auth.utils.logging import logging
from src.secret import (
    GOOGLE_DEFAULT_EMAIL,
    GOOGLE_APP_PASSWORD,
    GOOGLE_SMTP_SERVER,
    GOOGLE_SMTP_PORT,
)
from email.message import EmailMessage
from smtplib import (
    SMTPException,
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPDataError,
    SMTPConnectError,
)
from fastapi import HTTPException, status


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


async def gmail_configuration(
    email_receiver: EmailStr,
    email_subject: str,
    email_body: str,
    email_sender: EmailStr = GOOGLE_DEFAULT_EMAIL,
) -> EmailMessage | str:
    try:
        email = EmailMessage()
        email["From"] = email_sender
        email["To"] = email_receiver
        email["Subject"] = email_subject
        email.set_content(email_body)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(
                host=GOOGLE_SMTP_SERVER, port=int(GOOGLE_SMTP_PORT), context=context
            ) as smtp:
                smtp.login(user=GOOGLE_DEFAULT_EMAIL, password=GOOGLE_APP_PASSWORD)
                smtp.sendmail(
                    from_addr=GOOGLE_DEFAULT_EMAIL,
                    to_addrs=email_receiver,
                    msg=email.as_string(),
                )
        except SMTPAuthenticationError as e:
            logging.error(f"SMTPAuthenticationError: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SMTP Authentication failed. Please check your credentials.",
            )
        except SMTPRecipientsRefused as e:
            logging.error(f"SMTPRecipientsRefused: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMTP Recipients refused. The email address might be invalid.",
            )
        except SMTPSenderRefused as e:
            logging.error(f"SMTPSenderRefused: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMTP Sender refused. The sender's email address might be invalid.",
            )
        except SMTPDataError as e:
            logging.error(f"SMTPDataError: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMTP Data error occurred while sending the email.",
            )
        except SMTPConnectError as e:
            logging.error(f"SMTPConnectError: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to the SMTP server.",
            )
        except SMTPException as e:
            logging.error(f"SMTPException: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SMTP error occurred: {str(e)}",
            )
    except HTTPException as e:
        raise e
    except Exception as E:
        logging.error(f"Error after gmail_configuration: {E}")
    return smtp
