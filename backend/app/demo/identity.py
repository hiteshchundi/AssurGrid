"""Explicit fictional demo accounts; passwords supplied by the operator, never exported."""
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa

from app.db.schema import application_access, membership, organization, regulated_application, user_account
from app.modules.auth.security import hash_password, verify_password

ACCOUNTS = (
    ("admin", "Admin", ()),
    ("quality", "Quality", ()),
    ("owner", "Application Owner", ("NSB-LIMS-001", "NSB-QMS-003", "NSB-CDMS-002")),
    ("viewer", "Viewer", ("NSB-LIMS-001",)),
)


def seed_accounts(connection, passwords: dict[str, str]) -> int:
    if set(passwords) != {name for name, _, _ in ACCOUNTS} or any(not 12 <= len(p) <= 256 for p in passwords.values()):
        raise ValueError("Supply a 12–256 character password for each of the four demo accounts.")
    connection.execute(sa.text("LOCK TABLE organization, regulated_application, user_account, membership, application_access IN SHARE ROW EXCLUSIVE MODE"))
    org = connection.execute(sa.select(organization.c.id).where(organization.c.slug == "northstar-biopharma-demo")).scalar_one_or_none()
    if org is None:
        raise ValueError("Seed the fictional Northstar registry first.")
    inserted = 0
    for name, role, cis in ACCOUNTS:
        uid = uuid5(NAMESPACE_URL, f"assurgrid/demo/user/{name}")
        email = f"{name}@northstar.example.test"
        display = f"Synthetic {role}"
        apps = set(connection.execute(sa.select(regulated_application.c.id).where(
            regulated_application.c.organization_id == org, regulated_application.c.ci_id.in_(cis),
        )).scalars())
        if len(apps) != len(cis):
            raise ValueError("Required fictional applications are missing; no accounts were committed.")
        row = connection.execute(sa.select(user_account).where(user_account.c.id == uid)).mappings().one_or_none()
        if row:
            if (row["email"], row["display_name"], row["active"]) != (email, display, True) or not verify_password(passwords[name], row["password_hash"]):
                raise ValueError("Existing demo account differs; refusing to overwrite credentials or identity.")
        else:
            connection.execute(user_account.insert().values(id=uid, email=email, display_name=display, password_hash=hash_password(passwords[name])))
            inserted += 1
        memberships = connection.execute(sa.select(membership).where(membership.c.user_id == uid)).mappings().all()
        if memberships:
            if len(memberships) != 1 or (memberships[0]["organization_id"], memberships[0]["role"], memberships[0]["active"]) != (org, role, True):
                raise ValueError("Existing demo membership differs; refusing to overwrite access.")
        else:
            connection.execute(membership.insert().values(organization_id=org, user_id=uid, role=role))
        grants = set(connection.execute(sa.select(application_access.c.application_id).where(
            application_access.c.organization_id == org, application_access.c.user_id == uid,
        )).scalars())
        if grants - apps:
            raise ValueError("Existing demo application access differs; refusing to overwrite access.")
        for app_id in apps - grants:
            connection.execute(application_access.insert().values(organization_id=org, user_id=uid, application_id=app_id))
    return inserted
