"""Fictional organization policy fixtures, not regulatory requirements."""
from datetime import date, datetime, timezone
import json
from pathlib import Path
from uuid import uuid5

import sqlalchemy as sa

from app.db.schema import control_definition, governance_policy, organization, policy_control_rule, policy_version
from app.demo.registry import NAMESPACE, build_registry

SNAPSHOT_DATE = date(2026, 10, 12)
CREATED_AT = datetime(2026, 10, 12, tzinfo=timezone.utc)
SEED_VERSION = "policy-v1"
TABLES = (control_definition, governance_policy, policy_version, policy_control_rule)


def identity(key: str):
    return uuid5(NAMESPACE, f"policy-v1/{key}")


def build_policies() -> dict[str, list[dict]]:
    org = build_registry(SNAPSHOT_DATE)[0]
    controls = [dict(
        id=identity(f"control/{key}"), organization_id=org["id"], control_key=key, name=name,
        description="SYNTHETIC DEMO DATA — fictional organization control; not a mandated regulatory frequency.",
        active=True, created_at=CREATED_AT,
    ) for key, name in (
        ("PCR", "Periodic Compliance Review"), ("ACCESS_REVIEW", "Access Review"),
        ("ATR", "Audit Trail Review"), ("SUPPLIER_REVIEW", "Supplier Review"),
    )]
    profiles = [("HIGH_GXP", "Synthetic High-Criticality GxP", "High"),
                ("MEDIUM_GXP", "Synthetic Medium-Criticality GxP", "Medium")]
    policies = [dict(id=identity(f"policy/{key}"), organization_id=org["id"], policy_key=key,
                     name=name, created_at=CREATED_AT) for key, name, _ in profiles]
    versions, rules = [], []
    for key, _, criticality in profiles:
        for number in ([1, 2] if key == "HIGH_GXP" else [1]):
            version_id = identity(f"version/{key}/{number}")
            versions.append(dict(
                id=version_id, organization_id=org["id"], policy_id=identity(f"policy/{key}"), version_number=number,
                effective_from=date(2025, 1, 1) if number == 1 else date(2026, 7, 1),
                effective_to=date(2026, 7, 1) if key == "HIGH_GXP" and number == 1 else None,
                gxp_classification="GxP", criticality=criticality,
                change_reason=("SYNTHETIC DEMO DATA — initial illustrative organization profile." if number == 1 else
                               "SYNTHETIC DEMO DATA — fictional risk review shortens PCR from 24 to 12 calendar months; prior rules retained."),
                created_at=CREATED_AT,
            ))
            frequencies = ({"PCR": 24 if number == 1 else 12, "ACCESS_REVIEW": 3, "ATR": 3, "SUPPLIER_REVIEW": 24}
                           if key == "HIGH_GXP" else {"PCR": 24, "ACCESS_REVIEW": 6})
            for control_key, months in frequencies.items():
                rules.append(dict(
                    id=identity(f"rule/{key}/{number}/{control_key}"), organization_id=org["id"],
                    policy_version_id=version_id, control_definition_id=identity(f"control/{control_key}"),
                    frequency_months=months, due_soon_days=30, mandatory=True,
                    evidence_requirement=f"Synthetic {control_key} completion reference reviewed by the responsible role.",
                    created_at=CREATED_AT,
                ))
    return dict(control_definition=controls, governance_policy=policies, policy_version=versions, policy_control_rule=rules)


def export_policies(path: Path) -> None:
    data = build_policies()
    artifact = dict(label="SYNTHETIC DEMO DATA", seed_version=SEED_VERSION, snapshot_date=SNAPSHOT_DATE,
                    counts={name: len(rows) for name, rows in data.items()},
                    timestamp_meaning="Invented fixture initialization time; not historical approval evidence.",
                    policy_notice="Illustrative organization rules, not regulatory requirements.", tables=data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, default=str, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seed_policies(connection) -> dict[str, int]:
    """Caller owns one transaction; compare every existing policy row before inserts."""
    connection.execute(sa.text("LOCK TABLE organization, control_definition, governance_policy, policy_version, policy_control_rule IN SHARE ROW EXCLUSIVE MODE"))
    expected_org = build_registry(SNAPSHOT_DATE)[0]
    org = connection.execute(sa.select(organization).where(organization.c.id == expected_org["id"])).mappings().one_or_none()
    if org is None or any(org[key] != expected_org[key] for key in ("slug", "display_name", "timezone")):
        raise ValueError("Seed the matching fictional Northstar organization first; no policy data was overwritten.")
    data, missing = build_policies(), []
    for table in TABLES:
        expected = {row["id"]: row for row in data[table.name]}
        existing = connection.execute(sa.select(table)).mappings().all()
        if any(row["id"] not in expected or dict(row) != expected[row["id"]] for row in existing):
            raise ValueError("Database contains changed or non-seed policy records; no policy data was overwritten.")
        present = {row["id"] for row in existing}
        missing.append((table, [row for key, row in expected.items() if key not in present]))
    for table, rows in missing:
        if rows:
            connection.execute(table.insert(), rows)
    return {table.name: len(rows) for table, rows in missing}
