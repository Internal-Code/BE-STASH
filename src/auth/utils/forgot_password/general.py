import smtplib
import ssl
from email.mime.text import MIMEText
from email.message import EmailMessage
from pydantic import EmailStr
from src.auth.utils.logging import logging
from fastapi import HTTPException, status
from src.secret import (
    GOOGLE_DEFAULT_EMAIL,
    GOOGLE_APP_PASSWORD,
    GOOGLE_SMTP_SERVER,
    GOOGLE_SMTP_PORT,
)
from smtplib import (
    SMTPException,
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPDataError,
    SMTPConnectError,
)


# async def twilio_account(account_sid: str = TWILLIO_ACCOUNT_SID, account_auth_token: str = TWILLIO_AUTH_TOKEN) -> Client:
#     try:
#         twillio_client = await Client(account_sid, account_auth_token)
#         logging.info("Twilio client successfully authenticated.")
#     except TwilioRestException as e:
#         logging.error(f"Twilio REST API error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail="Failed to authenticate with Twilio. Please try again later.",
#         )
#     except TwilioException as e:
#         logging.error(f"Twilio error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An internal server error occurred with Twilio. Please try again later.",
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logging.error(f"Unexpected error during Twilio authentication: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An unexpected error occurred. Please try again later.",
#         )
#     return twillio_client

# async def send_twillio_messages(
#     message_receiver: str,
#     messages: str,
#     message_sender: str = TWILLIO_PHONE_NUMBER,
#     twillio_client: Client = twilio_account()
# ) -> str:
#     try:
#         messages = twillio_client.messages.create(
#             to=message_receiver,
#             from_=message_sender,
#             body=messages
#         )
#         return messages
#     except Exception as E:
#         pass
#     return None


async def send_gmail(
    email_receiver: EmailStr,
    email_subject: str,
    email_body: str,
    email_sender: EmailStr = GOOGLE_DEFAULT_EMAIL,
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
                host=GOOGLE_SMTP_SERVER, port=int(GOOGLE_SMTP_PORT), context=context
            ) as smtp:
                try:
                    logging.info(f"Email successfully sent into: {email_receiver}")
                    smtp.login(user=GOOGLE_DEFAULT_EMAIL, password=GOOGLE_APP_PASSWORD)
                    smtp.sendmail(
                        from_addr=GOOGLE_DEFAULT_EMAIL,
                        to_addrs=email_receiver,
                        msg=email.as_string(),
                    )
                except Exception as E:
                    logging.error(f"Error during sending smtp email: {E}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Internal Server Error: {E}.",
                    )
                finally:
                    smtp.close()
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
        logging.error(f"Unexpected error during Gmail SMTP authentication: {E}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later",
        )
    return smtp
