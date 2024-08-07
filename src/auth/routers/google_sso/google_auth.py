from fastapi import APIRouter, status
from starlette.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from src.secret import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from authlib.integrations.starlette_client import OAuth, OAuthError

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

router = APIRouter(tags=["google-sso"], prefix="/auth")


async def google_auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name="error.html", context={"request": request, "error": e.error}
        )
    user = token.get("userinfo")
    if user:
        request.session["user"] = dict(user)
    return RedirectResponse("/api/v1/google/welcome")


router.add_api_route(
    methods=["GET"],
    path="",
    endpoint=google_auth,
    status_code=status.HTTP_200_OK,
    summary="Login using google sso.",
)
