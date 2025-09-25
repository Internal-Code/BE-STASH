from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.secret import MIDDLEWARE_SECRET_KEY
from errors.register_error import register_exception_handlers
from starlette.middleware.sessions import SessionMiddleware
from src.common.routers import health, search_countries
from src.auth.routers.registration import (
    register_user,
    register_state,
    verify_otp,
    send_otp_method,
)

app = FastAPI(
    root_path="/api/v1",
    title="STASH Backend Application",
    description="Backend application for STASH.",
    version="0.1",
)

register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_SECRET_KEY)
app.include_router(health.router)
app.include_router(search_countries.router)
app.include_router(register_user.router)
app.include_router(register_state.router)
app.include_router(verify_otp.router)
app.include_router(send_otp_method.router)
