from fastapi import APIRouter, status, Request
from fastapi.templating import Jinja2Templates
from src.secret import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse

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


async def google_logout(request: Request):
    if "user" in request.session:
        request.session.pop("user")
    request.session.clear()
    return RedirectResponse("http://localhost:8000/api/v1/google/welcome")


router.add_api_route(
    methods=["GET"],
    path="/logout",
    endpoint=google_logout,
    status_code=status.HTTP_200_OK,
    summary="Logout using Google SSO.",
)
