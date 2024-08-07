from fastapi import APIRouter, status, Request
from fastapi.templating import Jinja2Templates
from src.secret import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from authlib.integrations.starlette_client import OAuth

templates = Jinja2Templates(directory="templates")
oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={
        "scope": "email openid profile",
        "redirect_url": "http://localhost:8000/api/v1/auth",
    },
)

router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_login(request: Request):
    url = request.url_for("google_auth")
    return await oauth.google.authorize_redirect(request, url)


router.add_api_route(
    methods=["GET"],
    path="/login",
    endpoint=google_sso_login,
    status_code=status.HTTP_200_OK,
    summary="Login using google sso.",
)
