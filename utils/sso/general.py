from utils.logger import logging
from authlib.integrations.starlette_client import OAuth
from src.secret import Config


config = Config()


async def google_oauth_configuration(
    name: str = "google",
    server_url: str = "https://accounts.google.com/.well-known/openid-configuration",
    scope: str = "email openid profile",
    redirect_url: str = "http://localhost:8000/api/v1/user/register/google/auth",
    prompt: str = "select_account",
) -> OAuth:
    try:
        oauth = OAuth()
        oauth.register(
            name=name,
            server_metadata_url=server_url,
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            client_kwargs={
                "scope": scope,
                "redirect_url": redirect_url,
                "prompt": prompt,
            },
        )
        return oauth
    except Exception as E:
        logging.error(f"Error after google_oauth_configuration: {E}")
    return None
