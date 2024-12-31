from fastapi import APIRouter, status, Request
from utils.sso.general import google_oauth_configuration

router = APIRouter(tags=["User Register"], prefix="/user/register")


async def google_sso_login_endpoint(request: Request):
    oauth = await google_oauth_configuration()
    url = request.url_for("google_sso_auth")
    return await oauth.google.authorize_redirect(request, url)


router.add_api_route(
    methods=["GET"],
    path="/google/login",
    endpoint=google_sso_login_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Login using google sso.",
)