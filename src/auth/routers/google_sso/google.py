from fastapi import APIRouter, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["google-sso"], prefix="/google")
templates = Jinja2Templates(directory="templates")


async def google_sso_root(request: Request) -> None:
    user = request.session.get("user")
    if user:
        return RedirectResponse("localhost:8000/api/v1/welcome")
    return templates.TemplateResponse(name="home.html", context={"request": request})


router.add_api_route(
    methods=["GET"],
    path="",
    endpoint=google_sso_root,
    status_code=status.HTTP_200_OK,
    summary="Google sso root endpoint.",
)
