from src.auth.utils.logging import logging
from authlib.integrations.starlette_client import OAuth
from src.secret import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


async def google_oauth_configuration(
    name: str = "google",
    server_url: str = "https://accounts.google.com/.well-known/openid-configuration",
    scope: str = "email openid profile",
    redirect_url: str = "http://localhost:8000/api/v1/google/auth",
    prompt: str = "select_account",
) -> OAuth:
    try:
        oauth = OAuth()
        oauth.register(
            name=name,
            server_metadata_url=server_url,
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
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
