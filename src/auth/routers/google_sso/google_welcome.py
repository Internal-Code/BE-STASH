from fastapi import APIRouter, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")
router = APIRouter(tags=["google-sso"], prefix="/google")


async def welcome(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("localhost:8000/api/v1/google")
    return templates.TemplateResponse(
        name="welcome.html", context={"request": request, "user": user}
    )


router.add_api_route(
    methods=["GET"],
    path="/welcome",
    endpoint=welcome,
    status_code=status.HTTP_200_OK,
    summary="Google SSO welcome page.",
)
