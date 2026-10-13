import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.auth.router import Principal, get_principal
from . import repository
from .schemas import PolicyFilters, PolicyHistory, PolicyPage, PolicyResolution, ResolutionDate

router = APIRouter(tags=["policies"])
logger = logging.getLogger(__name__)


def require_policy_reader(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
    if principal.role not in ("Admin", "Quality"):
        raise HTTPException(403, "Policy administration access required.")
    return principal


def read(operation, *args):
    try:
        return operation(*args)
    except SQLAlchemyError as error:
        logger.warning("Policy read failed (%s)", type(error).__name__)
        raise HTTPException(503, "Policy configuration is temporarily unavailable.") from None


@router.get("/policies", response_model=PolicyPage)
def list_policies(filters: Annotated[PolicyFilters, Query()], response: Response,
                  principal: Annotated[Principal, Depends(require_policy_reader)],
                  session: Annotated[Session, Depends(get_session)]):
    response.headers["Cache-Control"] = "no-store"
    return read(repository.list_policies, session, principal, filters)


@router.get("/policies/{policy_id}", response_model=PolicyHistory)
def policy_history(policy_id: UUID, response: Response,
                   principal: Annotated[Principal, Depends(require_policy_reader)],
                   session: Annotated[Session, Depends(get_session)]):
    result = read(repository.history, session, principal, policy_id)
    if result is None: raise HTTPException(404, "Policy not found.")
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/applications/{application_id}/policy", response_model=PolicyResolution)
def application_policy(application_id: UUID, dates: Annotated[ResolutionDate, Query()], response: Response,
                       principal: Annotated[Principal, Depends(get_principal)],
                       session: Annotated[Session, Depends(get_session)]):
    result = read(repository.resolve, session, principal, application_id, dates.as_of)
    if result is None: raise HTTPException(404, "Application not found.")
    response.headers["Cache-Control"] = "no-store"
    return result
