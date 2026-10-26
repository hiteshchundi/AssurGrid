"""Explicit reproducible deadline fixtures, not invented historical completions."""
from datetime import date, timedelta
from uuid import uuid5

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from app.db.schema import governance_obligation, membership
from app.demo.registry import NAMESPACE, build_registry
from app.demo.policies import build_policies, SNAPSHOT_DATE
from app.modules.governance.scheduling import add_months, generation_key


def seed_obligations(connection):
    org, apps = build_registry(SNAPSHOT_DATE)
    policies = build_policies()
    versions = [v for v in policies["policy_version"] if v["effective_to"] is None]
    owner = connection.execute(sa.select(membership.c.user_id).where(
        membership.c.organization_id == org["id"], membership.c.role == "Application Owner")).scalar_one_or_none()
    inserted = 0
    for index, app in enumerate(apps):
        if app["lifecycle_state"] != "Operational" or app["gxp_classification"] != "GxP":
            continue
        version = next((v for v in versions if v["criticality"] == app["criticality"]), None)
        if version is None:
            continue
        rules = [r for r in policies["policy_control_rule"] if r["policy_version_id"] == version["id"]]
        for number, rule in enumerate(rules):
            # Frozen, explicitly fictional schedule: overdue, near, and later deadlines.
            due = date(2026, 10, 26) + timedelta(days=(-14, 15, 75, 120)[(index + number) % 4])
            start = add_months(due, -rule["frequency_months"])
            key = generation_key(app["id"], rule["id"], start)
            result = connection.execute(insert(governance_obligation).values(
                id=uuid5(NAMESPACE, f"obligation-v1/{key}"), organization_id=org["id"], application_id=app["id"],
                policy_control_rule_id=rule["id"], policy_version_id=version["id"],
                **{k: rule[k] for k in ("control_definition_id", "frequency_months", "due_soon_days", "mandatory", "evidence_requirement")},
                window_start=start, due_date=due, generation_key=key,
                assigned_owner_id=owner if index < 3 else None,
            ).on_conflict_do_nothing(index_elements=["organization_id", "generation_key"]).returning(governance_obligation.c.id))
            inserted += int(result.scalar_one_or_none() is not None)
    return inserted
