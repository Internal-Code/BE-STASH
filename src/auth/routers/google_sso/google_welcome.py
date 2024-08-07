from fastapi import APIRouter, status, Request
from fastapi.templating import Jinja2Templates
from src.secret import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse

print(GOOGLE_CLIENT_SECRET)
print(GOOGLE_CLIENT_ID)

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


async def welcome(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/api/v1/google")
    return templates.TemplateResponse(
        name="welcome.html", context={"request": request, "user": user}
    )


router.add_api_route(
    methods=["GET"],
    path="/welcome",
    endpoint=welcome,
    status_code=status.HTTP_200_OK,
    summary="Login using google sso.",
)
