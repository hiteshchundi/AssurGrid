import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.auth.router import Principal, get_principal
from app.db.session import get_session
from app.modules.applications import repository
from app.modules.applications.schemas import Application, ApplicationFilters, ApplicationPage

router = APIRouter(prefix="/applications", tags=["applications"])
logger = logging.getLogger(__name__)


@router.get("", response_model=ApplicationPage, responses={503: {"description": "Registry unavailable"}})
def list_applications(
    filters: Annotated[ApplicationFilters, Query()],
    principal: Annotated[Principal, Depends(get_principal)],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        return repository.list_applications(session, principal.organization_id, filters, principal)
    except SQLAlchemyError as error:
        logger.warning("Application registry read failed (%s)", type(error).__name__)
        raise HTTPException(status_code=503, detail="Application registry is temporarily unavailable.") from None


@router.get("/{application_id}", response_model=Application, responses={
    404: {"description": "Application not found in the configured organization"},
    503: {"description": "Registry unavailable"},
})
def get_application(
    application_id: UUID,
    principal: Annotated[Principal, Depends(get_principal)],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        application = repository.get_application(session, principal.organization_id, application_id, principal)
    except SQLAlchemyError as error:
        logger.warning("Application registry read failed (%s)", type(error).__name__)
        raise HTTPException(status_code=503, detail="Application registry is temporarily unavailable.") from None
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application
