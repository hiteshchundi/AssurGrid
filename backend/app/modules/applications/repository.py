from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.schema import regulated_application as application
from app.modules.applications.schemas import ApplicationFilters


def list_applications(session: Session, organization_id: UUID, filters: ApplicationFilters):
    conditions = [application.c.organization_id == organization_id]
    if filters.search:
        conditions.append(sa.or_(
            application.c.ci_id.icontains(filters.search, autoescape=True),
            application.c.name.icontains(filters.search, autoescape=True),
        ))
    for column, value in (
        (application.c.gxp_classification, filters.classification),
        (application.c.criticality, filters.criticality),
        (application.c.lifecycle_state, filters.lifecycle_state),
        (application.c.validation_state, filters.validation_state),
    ):
        if value is not None:
            conditions.append(column == value)

    # One statement gives the page and total the same PostgreSQL snapshot.
    # The outer join retains the count even when the requested page is empty.
    filtered = sa.select(application).where(*conditions).cte("filtered_applications")
    page = (
        sa.select(filtered).order_by(filtered.c.ci_id, filtered.c.id)
        .offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        .subquery("application_page")
    )
    count = sa.select(sa.func.count().label("total")).select_from(filtered).subquery("application_count")
    rows = session.execute(
        sa.select(count.c.total, *page.c).select_from(count.outerjoin(page, sa.true()))
        .order_by(page.c.ci_id, page.c.id)
    ).mappings().all()
    return {
        "items": [{key: value for key, value in row.items() if key != "total"} for row in rows if row["id"] is not None],
        "total": rows[0]["total"], "page": filters.page, "page_size": filters.page_size,
    }


def get_application(session: Session, organization_id: UUID, application_id: UUID):
    return session.execute(sa.select(application).where(
        application.c.organization_id == organization_id,
        application.c.id == application_id,
    )).mappings().one_or_none()
