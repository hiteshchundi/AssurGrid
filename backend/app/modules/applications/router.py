import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.modules.applications import repository
from app.modules.applications.schemas import Application, ApplicationFilters, ApplicationPage

router = APIRouter(prefix="/applications", tags=["applications"])
logger = logging.getLogger(__name__)


def get_registry_organization(settings: Annotated[Settings, Depends(get_settings)]) -> UUID:
    # Temporary local-demo boundary; replace with session membership in Slice 06.
    if settings.app_env != "development" or settings.demo_registry_organization_id is None:
        raise HTTPException(status_code=503, detail="Demo registry is disabled or its organization is not configured.")
    return settings.demo_registry_organization_id


@router.get("", response_model=ApplicationPage, responses={503: {"description": "Registry unavailable"}})
def list_applications(
    filters: Annotated[ApplicationFilters, Query()],
    organization_id: Annotated[UUID, Depends(get_registry_organization)],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        return repository.list_applications(session, organization_id, filters)
    except SQLAlchemyError as error:
        logger.warning("Application registry read failed (%s)", type(error).__name__)
        raise HTTPException(status_code=503, detail="Application registry is temporarily unavailable.") from None


@router.get("/{application_id}", response_model=Application, responses={
    404: {"description": "Application not found in the configured organization"},
    503: {"description": "Registry unavailable"},
})
def get_application(
    application_id: UUID,
    organization_id: Annotated[UUID, Depends(get_registry_organization)],
    session: Annotated[Session, Depends(get_session)],
):
    try:
        application = repository.get_application(session, organization_id, application_id)
    except SQLAlchemyError as error:
        logger.warning("Application registry read failed (%s)", type(error).__name__)
        raise HTTPException(status_code=503, detail="Application registry is temporarily unavailable.") from None
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application
