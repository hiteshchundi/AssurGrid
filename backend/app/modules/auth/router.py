"""Server-managed sessions; permissions are read fresh from current membership."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hmac
import secrets
from typing import Annotated
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.schema import browser_session, membership, user_account
from app.db.session import get_session
from .security import hash_password, token_hash, verify_password

class AuthRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_validation(request: Request):
            try:
                return await handler(request)
            except RequestValidationError:
                # FastAPI's default validation response can echo password input.
                raise HTTPException(422, "Invalid authentication request.") from None
        return safe_validation


router = APIRouter(prefix="/auth", tags=["auth"], route_class=AuthRoute)
COOKIE = "assurgrid_session"
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    organization_id: UUID
    role: str
    session_id: UUID
    csrf_token_hash: str


def now() -> datetime:
    return datetime.now(timezone.utc)


def require_origin(request: Request, settings: Settings) -> None:
    if request.headers.get("origin") != str(settings.frontend_origin).rstrip("/"):
        raise HTTPException(403, "Untrusted request origin.")


def get_principal(request: Request, session: Annotated[Session, Depends(get_session)]) -> Principal:
    token = request.cookies.get(COOKIE, "")
    if not token or len(token) > 128:
        raise HTTPException(401, "Authentication required.")
    try:
        row = session.execute(sa.select(
            browser_session.c.id, browser_session.c.user_id, browser_session.c.organization_id,
            browser_session.c.csrf_token_hash, membership.c.role,
        ).select_from(browser_session.join(membership, sa.and_(
            browser_session.c.organization_id == membership.c.organization_id,
            browser_session.c.user_id == membership.c.user_id,
        )).join(user_account, user_account.c.id == membership.c.user_id)).where(
            browser_session.c.token_hash == token_hash(token),
            browser_session.c.revoked_at.is_(None), browser_session.c.expires_at > now(),
            membership.c.active.is_(True), user_account.c.active.is_(True),
        )).mappings().one_or_none()
    except SQLAlchemyError:
        raise HTTPException(503, "Authentication is temporarily unavailable.") from None
    if row is None:
        raise HTTPException(401, "Authentication required.")
    return Principal(row["user_id"], row["organization_id"], row["role"], row["id"], row["csrf_token_hash"])


def require_csrf(request: Request, principal: Principal, settings: Settings) -> None:
    require_origin(request, settings)
    token = request.headers.get("x-csrf-token", "")
    if not token or len(token) > 128 or not hmac.compare_digest(token_hash(token), principal.csrf_token_hash):
        raise HTTPException(403, "Invalid CSRF token.")


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256, repr=False)


def create_browser_session(session, request, response, settings, user_id):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    created = now()
    old_token = request.cookies.get(COOKIE)
    if old_token and len(old_token) <= 128:
        session.execute(browser_session.update().where(
            browser_session.c.token_hash == token_hash(old_token), browser_session.c.revoked_at.is_(None),
        ).values(revoked_at=created))
    session.execute(browser_session.delete().where(browser_session.c.expires_at < created))
    session.execute(browser_session.insert().values(
        organization_id=settings.demo_registry_organization_id, user_id=user_id,
        token_hash=token_hash(token), csrf_token_hash=token_hash(csrf),
        created_at=created, expires_at=created + timedelta(hours=8),
    ))
    session.commit()
    response.set_cookie(COOKIE, token, max_age=28800, httponly=True,
                        secure=settings.frontend_origin.scheme == "https", samesite="strict", path="/api/v1")
    response.headers["Cache-Control"] = "no-store"
    return {"csrf_token": csrf}


class DemoLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona: Literal["admin", "quality", "owner", "viewer"]


@router.get("/options")
def options(settings: Annotated[Settings, Depends(get_settings)], response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"public_demo_enabled": settings.public_demo_enabled}


@router.post("/demo")
def demo_login(body: DemoLogin, request: Request, response: Response,
               settings: Annotated[Settings, Depends(get_settings)],
               session: Annotated[Session, Depends(get_session)]):
    # Explicit public sandbox. These are synthetic personas, never an identity provider.
    if not settings.public_demo_enabled or settings.demo_registry_organization_id is None:
        raise HTTPException(503, "Public demo is disabled.")
    require_origin(request, settings)
    try:
        from app.db.schema import organization
        user = session.execute(sa.select(user_account.c.id).join(membership,
            membership.c.user_id == user_account.c.id).join(organization,
            organization.c.id == membership.c.organization_id).where(
                organization.c.id == settings.demo_registry_organization_id,
                organization.c.slug == "northstar-biopharma-demo",
                user_account.c.email == f"{body.persona}@northstar.example.test",
                user_account.c.active.is_(True), membership.c.active.is_(True),
        )).scalar_one_or_none()
        if user is None:
            raise HTTPException(503, "The demo is not initialized yet.")
        return create_browser_session(session, request, response, settings, user)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "The demo is temporarily unavailable.") from None


@router.post("/login")
def login(body: Login, request: Request, response: Response,
          settings: Annotated[Settings, Depends(get_settings)],
          session: Annotated[Session, Depends(get_session)]):
    # Password login is intentionally limited to this local prototype.
    if settings.app_env != "development" or settings.demo_registry_organization_id is None:
        raise HTTPException(503, "Prototype login is disabled.")
    require_origin(request, settings)
    try:
        row = session.execute(sa.select(user_account.c.id, user_account.c.password_hash).join(
            membership, membership.c.user_id == user_account.c.id,
        ).where(user_account.c.email == body.email.strip().lower(), user_account.c.active.is_(True),
                membership.c.active.is_(True),
                membership.c.organization_id == settings.demo_registry_organization_id)).mappings().one_or_none()
        valid = verify_password(body.password, row["password_hash"] if row else DUMMY_PASSWORD_HASH)
        if row is None or not valid:
            raise HTTPException(401, "Invalid email or password.")
        return create_browser_session(session, request, response, settings, row["id"])
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Authentication is temporarily unavailable.") from None


@router.get("/me")
def me(response: Response, principal: Annotated[Principal, Depends(get_principal)]):
    response.headers["Cache-Control"] = "no-store"
    return {"user_id": principal.user_id, "organization_id": principal.organization_id, "role": principal.role}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response,
           principal: Annotated[Principal, Depends(get_principal)],
           settings: Annotated[Settings, Depends(get_settings)],
           session: Annotated[Session, Depends(get_session)]):
    require_csrf(request, principal, settings)
    try:
        session.execute(browser_session.update().where(browser_session.c.id == principal.session_id).values(revoked_at=now()))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Authentication is temporarily unavailable.") from None
    response.delete_cookie(COOKIE, path="/api/v1", httponly=True,
                           secure=settings.frontend_origin.scheme == "https", samesite="strict")
    response.headers["Cache-Control"] = "no-store"


@router.post("/csrf")
def refresh_csrf(request: Request, response: Response,
                 principal: Annotated[Principal, Depends(get_principal)],
                 settings: Annotated[Settings, Depends(get_settings)],
                 session: Annotated[Session, Depends(get_session)]):
    # Origin protects this bootstrap endpoint; no token is persisted by the browser.
    require_origin(request, settings)
    csrf = secrets.token_urlsafe(32)
    try:
        session.execute(browser_session.update().where(browser_session.c.id == principal.session_id).values(csrf_token_hash=token_hash(csrf)))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Authentication is temporarily unavailable.") from None
    response.headers["Cache-Control"] = "no-store"
    return {"csrf_token": csrf}
