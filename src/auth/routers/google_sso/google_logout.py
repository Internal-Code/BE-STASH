from fastapi import APIRouter, status
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")

router = APIRouter(tags=["google-sso"], prefix="/google")


async def google_logout(request: Request):
    request.session.pop("user", None)
    request.session.clear()
    return RedirectResponse("http://localhost:8000/api/v1/google")


router.add_api_route(
    methods=["GET"],
    path="/logout",
    endpoint=google_logout,
    status_code=status.HTTP_200_OK,
    summary="Logout using Google SSO.",
)
