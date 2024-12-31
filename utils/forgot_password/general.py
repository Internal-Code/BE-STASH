import ssl
import smtplib
from pydantic import EmailStr
from email.mime.text import MIMEText
from email.message import EmailMessage
from utils.logger import logging
from src.secret import Config
from smtplib import (
    SMTPException,
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPDataError,
    SMTPConnectError,
)
from utils.custom_error import (
    AuthenticationFailed,
    FinanceTrackerApiError,
    ServiceError,
    EntityDoesNotMatchedError,
)


config = Config()


async def send_gmail(
    email_receiver: EmailStr,
    email_subject: str,
    email_body: str,
    email_sender: EmailStr = config.GOOGLE_DEFAULT_EMAIL,
) -> EmailMessage:
    try:
        email = EmailMessage()
        email["From"] = email_sender
        email["To"] = email_receiver
        email["Subject"] = email_subject
        email.set_content(email_body)
        email.set_content(MIMEText(email_body, "html"))

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(
                host=config.GOOGLE_SMTP_SERVER,
                port=int(config.GOOGLE_SMTP_PORT),
                context=context,
            ) as smtp:
                try:
                    logging.info(f"Email successfully sent into: {email_receiver}")
                    smtp.login(
                        user=config.GOOGLE_DEFAULT_EMAIL,
                        password=config.GOOGLE_APP_PASSWORD,
                    )
                    smtp.sendmail(
                        from_addr=config.GOOGLE_DEFAULT_EMAIL,
                        to_addrs=email_receiver,
                        msg=email.as_string(),
                    )
                except Exception as E:
                    logging.error(f"Error during sending smtp email: {E}")
                    raise ServiceError(detail=f"SMTP Error: {E}.", name="Google SMTP")
                finally:
                    smtp.close()
        except SMTPAuthenticationError as e:
            logging.error(f"SMTPAuthenticationError: {e}")
            raise AuthenticationFailed(
                detail="SMTP Authentication failed. Please check your credentials."
            )
        except SMTPRecipientsRefused as e:
            logging.error(f"SMTPRecipientsRefused: {e}")
            raise EntityDoesNotMatchedError(
                detail="SMTP Recipients refused. The email address might be invalid."
            )
        except SMTPSenderRefused as e:
            logging.error(f"SMTPSenderRefused: {e}")
            raise EntityDoesNotMatchedError(
                detail="SMTP Sender refused. The sender's email address might be invalid."
            )
        except SMTPDataError as e:
            logging.error(f"SMTPDataError: {e}")
            raise ServiceError(
                detail="SMTP Data error occurred while sending the email.",
                name="Google SMTP",
            )
        except SMTPConnectError as e:
            logging.error(f"SMTPConnectError: {e}")
            raise ServiceError(detail="Failed to connect to the SMTP server.", name="Google SMTP")
        except SMTPException as e:
            logging.error(f"SMTPException: {e}")
            raise ServiceError(detail=f"SMTP error occurred: {str(e)}", name="Google SMTP")
    except FinanceTrackerApiError as FTE:
        raise FTE
    except Exception as E:
        logging.error(f"Unexpected error during Gmail SMTP authentication: {E}")
        raise ServiceError(
            detail="An unexpected error occurred. Please try again later",
            name="Google SMTP",
        )
    return smtp
