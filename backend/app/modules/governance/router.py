"""Role-scoped oversight and atomic completion; no external document execution."""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.schema import (control_definition as control, governance_obligation as obligation,
    obligation_completion as completion, organization, policy_version, user_account,
    regulated_application as application)
from app.db.session import get_session
from app.modules.applications.repository import access_condition, get_application
from app.modules.auth.router import Principal, get_principal, require_csrf
from .scheduling import add_months, generation_key, obligation_status

router = APIRouter(prefix="/governance", tags=["governance"])


def organization_date(session, principal):
    timezone = session.execute(sa.select(organization.c.timezone).where(
        organization.c.id == principal.organization_id)).scalar_one()
    return datetime.now(ZoneInfo(timezone)).date(), timezone


def read_obligations(session, principal, as_of, application_id=None):
    query = sa.select(
        obligation, application.c.ci_id, application.c.name.label("application_name"),
        control.c.name.label("control_name"), control.c.control_key,
        policy_version.c.version_number,
        completion.c.completed_at, completion.c.evidence_reference, completion.c.notes,
        user_account.c.display_name.label("completed_by"),
    ).select_from(obligation.join(application, sa.and_(
        application.c.id == obligation.c.application_id,
        application.c.organization_id == obligation.c.organization_id))
        .join(control, control.c.id == obligation.c.control_definition_id)
        .join(policy_version, policy_version.c.id == obligation.c.policy_version_id)
        .outerjoin(completion, completion.c.obligation_id == obligation.c.id)
        .outerjoin(user_account, user_account.c.id == completion.c.completed_by_id)
    ).where(obligation.c.organization_id == principal.organization_id, access_condition(principal),
            obligation.c.superseded_by_id.is_(None))
    if application_id:
        query = query.where(obligation.c.application_id == application_id)
    rows = session.execute(query.order_by(obligation.c.due_date, application.c.ci_id, control.c.control_key)).mappings().all()
    return [dict(row, status=obligation_status(row["due_date"], row["due_soon_days"], as_of,
                     row["completed_at"] is not None), days_remaining=(row["due_date"] - as_of).days)
            for row in rows]


def health(items):
    mandatory = [item for item in items if item["mandatory"] and item["status"] != "Completed"]
    if not mandatory:
        return "Not scheduled"
    if any(item["status"] == "Overdue" for item in mandatory):
        return "Overdue"
    if any(item["status"] == "Due soon" for item in mandatory):
        return "Due soon"
    return "Current"


@router.get("")
def overview(principal: Annotated[Principal, Depends(get_principal)],
             session: Annotated[Session, Depends(get_session)], response: Response,
             application_id: UUID | None = None,
             status: Literal["Overdue", "Due soon", "Upcoming", "Completed"] | None = None):
    response.headers["Cache-Control"] = "no-store"
    try:
        if application_id and get_application(session, principal.organization_id, application_id, principal) is None:
            raise HTTPException(404, "Application not found.")
        as_of, timezone = organization_date(session, principal)
        items = read_obligations(session, principal, as_of, application_id)
        apps = session.execute(sa.select(application.c.id, application.c.ci_id, application.c.name,
            application.c.lifecycle_state, application.c.validation_state).where(
                application.c.organization_id == principal.organization_id, access_condition(principal),
                *([application.c.id == application_id] if application_id else []))
            .order_by(application.c.ci_id)).mappings().all()
        grouped = {}
        for item in items:
            grouped.setdefault(item["application_id"], []).append(item)
        portfolio = [dict(row, governance_health=health(grouped.get(row["id"], []))) for row in apps]
        counts = {value: sum(item["status"] == value for item in items)
                  for value in ("Overdue", "Due soon", "Upcoming", "Completed")}
        return dict(as_of=as_of, timezone=timezone, counts=counts, applications=portfolio,
                    items=[item for item in items if status is None or item["status"] == status])
    except SQLAlchemyError:
        raise HTTPException(503, "Governance is temporarily unavailable.") from None


class CompletionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_reference: str = Field(min_length=1, max_length=500)
    notes: str = Field(min_length=1, max_length=2000)

    @field_validator("evidence_reference", "notes")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Enter a nonblank value")
        return value.strip()


@router.post("/{obligation_id}/complete", status_code=201)
def complete(obligation_id: UUID, body: CompletionInput, request: Request, response: Response,
             principal: Annotated[Principal, Depends(get_principal)],
             session: Annotated[Session, Depends(get_session)],
             settings: Annotated[Settings, Depends(get_settings)]):
    require_csrf(request, principal, settings)
    if principal.role not in ("Admin", "Quality", "Application Owner"):
        raise HTTPException(403, "Your role cannot record completion.")
    try:
        row = session.execute(sa.select(obligation).join(application, sa.and_(
            application.c.id == obligation.c.application_id,
            application.c.organization_id == obligation.c.organization_id)).where(
                obligation.c.id == obligation_id, obligation.c.organization_id == principal.organization_id,
                access_condition(principal)).with_for_update(of=obligation)).mappings().one_or_none()
        if row is None:
            raise HTTPException(404, "Obligation not found.")
        if row["superseded_by_id"] is not None or session.execute(sa.select(completion.c.id).where(
            completion.c.obligation_id == obligation_id)).scalar_one_or_none():
            raise HTTPException(409, "This obligation has already been completed or superseded. Refresh the view.")
        as_of, _ = organization_date(session, principal)
        if row["window_start"] > as_of:
            raise HTTPException(409, "This review window has not started yet.")
        session.execute(completion.insert().values(organization_id=principal.organization_id,
            obligation_id=obligation_id, completed_by_id=principal.user_id, **body.model_dump()))
        # Keep the pinned policy snapshot and fixed cadence; late completion never moves the old deadline.
        next_start = row["due_date"]
        next_due = add_months(next_start, row["frequency_months"])
        next_id = session.execute(obligation.insert().values(
            **{key: row[key] for key in ("organization_id", "application_id", "policy_control_rule_id",
                "policy_version_id", "control_definition_id", "frequency_months", "due_soon_days", "mandatory",
                "evidence_requirement", "assigned_owner_id")},
            window_start=next_start, due_date=next_due,
            generation_key=generation_key(row["application_id"], row["policy_control_rule_id"], next_start),
        ).returning(obligation.c.id)).scalar_one()
        session.commit()
        response.headers["Cache-Control"] = "no-store"
        return {"status": "Completed", "next_obligation_id": next_id, "next_due_date": next_due}
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Completion could not be saved. Refresh before trying again.") from None
