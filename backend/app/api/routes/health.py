import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_session

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


class Liveness(BaseModel):
    status: Literal["ok"] = "ok"


class Readiness(BaseModel):
    status: Literal["ready", "not_ready"]
    database: Literal["connected", "unavailable"]


@router.get("/live", response_model=Liveness)
def live() -> Liveness:
    return Liveness()


@router.get("/ready", response_model=Readiness, responses={503: {"model": Readiness}})
def ready(session: Annotated[Session, Depends(get_session)]) -> Readiness | JSONResponse:
    try:
        session.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as error:
        # Log the error type without exposing connection strings or credentials.
        logger.warning("Database readiness failed (%s)", type(error).__name__)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )
    return Readiness(status="ready", database="connected")
