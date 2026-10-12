from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.applications.router import router as applications_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(applications_router)

api_router.include_router(auth_router)
