from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="AssurGrid", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.frontend_origin).rstrip("/")],
    allow_methods=["GET"],
    allow_headers=["Accept"],
)
app.include_router(api_router)
