from fastapi import APIRouter, status
from starlette.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from src.auth.utils.sso.general import google_oauth_configuration
from authlib.integrations.starlette_client import OAuthError

templates = Jinja2Templates(directory="templates")
router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_sso_auth(request: Request):
    try:
        oauth = await google_oauth_configuration()
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name="error.html", context={"request": request, "error": e.error}
        )
    user = token.get("userinfo")
    if user:
        request.session["user"] = dict(user)
    return RedirectResponse("http://localhost:8000/api/v1/google/welcome")


router.add_api_route(
    methods=["GET"],
    path="/auth",
    endpoint=google_sso_auth,
    status_code=status.HTTP_200_OK,
    summary="Authorization using google sso.",
    name="google_sso_auth",
)
