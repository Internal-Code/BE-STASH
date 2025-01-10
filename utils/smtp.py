import ssl
import smtplib
from pydantic import EmailStr
from email.message import EmailMessage
from utils.logger import logging
from src.secret import Config
from smtplib import (
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPDataError,
    SMTPConnectError,
)
from utils.custom_error import (
    AuthenticationFailed,
    ServiceError,
    EntityDoesNotMatchedError,
)


config = Config()


async def send_gmail(
    email_receiver: EmailStr,
    email_subject: str,
    email_body: str,
    email_sender: EmailStr = config.GOOGLE_DEFAULT_EMAIL,
) -> None:
    email = EmailMessage()
    email["From"] = email_sender
    email["To"] = email_receiver
    email["Subject"] = email_subject
    email.set_content(email_body, subtype="html")
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host=config.GOOGLE_SMTP_SERVER, port=int(config.GOOGLE_SMTP_PORT), context=context) as smtp:
        try:
            smtp.login(user=config.GOOGLE_DEFAULT_EMAIL, password=config.GOOGLE_APP_PASSWORD)
            smtp.sendmail(email)
            logging.info(f"Email successfully sent into {email_receiver}")
        except SMTPAuthenticationError:
            raise AuthenticationFailed(detail="SMTP Authentication failed. Please check your credentials.")
        except SMTPRecipientsRefused:
            raise EntityDoesNotMatchedError(detail="SMTP Recipients refused. The email address might be invalid.")
        except SMTPSenderRefused:
            raise EntityDoesNotMatchedError(detail="SMTP Sender refused. The sender's email address might be invalid.")
        except SMTPDataError:
            raise ServiceError(detail="SMTP Data error occurred while sending the email.", name="Google SMTP")
        except SMTPConnectError:
            raise ServiceError(detail="Failed to connect to the SMTP server.", name="Google SMTP")
        except Exception as E:
            logging.error(f"Error during sending smtp email: {E}")
            raise ServiceError(detail=f"SMTP Error: {E}.", name="Google SMTP")
        finally:
            smtp.close()
    return None


async def send_account_info_to_email(email: EmailStr, full_name: str, phone_number: str, pin: str) -> None:
    logging.info("Send account information to email.")
    email_body = (
        f"Dear {full_name},<br><br>"
        f"We are pleased to inform you that your new account has been successfully registered.<br><br>"
        f"You can now log in using the following credentials:<br><br>"
        f"Phone Number: <strong>{phone_number}</strong><br>"
        f"PIN: <strong>{pin}</strong><br><br>"
        f"Please ensure that you keep your account information secure.<br><br>"
        f"Best regards,<br>"
        f"STASH Support Team"
    )

    try:
        await send_gmail(
            email_subject="Success Registered STASH Account!",
            email_receiver=email,
            email_body=email_body,
        )
    except Exception:
        raise ServiceError(detail="Failed to send accouunt info via email.", name="Whatsapp API")
