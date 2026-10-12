"""Deterministic registry fixtures and an insert-only seed operation."""

import csv
from datetime import date, datetime, time, timezone
import hashlib
import json
from pathlib import Path
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from sqlalchemy.engine import Connection, URL, make_url

from app.db.schema import organization, regulated_application

DEMO_TIMEZONE = "Asia/Kolkata"
SEED_VERSION = "registry-v1"
NAMESPACE = UUID("bb873e69-f2d4-56a7-86f8-4c7ee8f70452")

# Ordered fictional identities are intentional, not random rows or real CI exports.
CATALOG = (
    ("LIMS", "LIMS", "Laboratory Information System"),
    ("CDMS", "Clinical", "Clinical Data Management"),
    ("QMS", "QMS", "Quality Management"),
    ("MES", "Manufacturing", "Manufacturing Execution"),
    ("SAFETY", "Safety", "Safety Case Management"),
    ("ERP", "Enterprise", "Internal ERP"),
    ("ATR", "Analytics", "Audit Trail Analytics"),
    ("ELN", "Laboratory", "Electronic Laboratory Notebook"),
    ("SDMS", "Laboratory", "Scientific Data Management"),
    ("STABILITY", "Laboratory", "Stability Study Tracking"),
    ("SAMPLE", "Laboratory", "Sample Chain of Custody"),
    ("CALIBRATION", "Laboratory", "Instrument Calibration"),
    ("CTMS", "Clinical", "Clinical Trial Management"),
    ("RTSM", "Clinical", "Randomization and Supply"),
    ("EPRO", "Clinical", "Participant Outcome Capture"),
    ("ETMF", "Clinical", "Trial Master File Index"),
    ("CLINREVIEW", "Clinical", "Clinical Review Workspace"),
    ("BIOSTATS", "Analytics", "Biostatistics Workspace"),
    ("RIM", "Regulatory", "Regulatory Information Management"),
    ("SUBMIT", "Regulatory", "Submission Assembly"),
    ("LABEL", "Regulatory", "Product Label Review"),
    ("COMMIT", "Regulatory", "Regulatory Commitment Tracking"),
    ("SIGNAL", "Safety", "Safety Signal Review"),
    ("LITERATURE", "Safety", "Safety Literature Screening"),
    ("MEDQUERY", "Safety", "Medical Query Tracking"),
    ("AGGREPORT", "Safety", "Aggregate Safety Reporting"),
    ("BATCH", "Manufacturing", "Batch Record Review"),
    ("WEIGH", "Manufacturing", "Weigh and Dispense"),
    ("ENVIRONMENT", "Manufacturing", "Environmental Monitoring"),
    ("SERIAL", "Manufacturing", "Serialization Tracking"),
    ("COLDCHAIN", "Manufacturing", "Cold Chain Monitoring"),
    ("EQUIPMENT", "Manufacturing", "Equipment Maintenance"),
    ("DEVIATION", "QMS", "Deviation Investigation"),
    ("TRAINING", "QMS", "Quality Training Records"),
    ("SUPPLIER", "QMS", "Supplier Quality Review"),
    ("COMPLAINT", "QMS", "Product Complaint Tracking"),
    ("AUDIT", "QMS", "Quality Audit Planning"),
    ("DOCINDEX", "QMS", "Controlled Document Index"),
    ("LABTRENDS", "Analytics", "Laboratory Trend Review"),
    ("PROCESS", "Analytics", "Process Performance Review"),
    ("DATATRANSFER", "Clinical", "Study Data Transfer"),
    ("ARCHIVE", "Regulatory", "Regulatory Archive Index"),
    ("PORTFOLIO", "Enterprise", "Research Portfolio Planning"),
    ("PROCURE", "Enterprise", "Office Procurement"),
    ("CAPACITY", "Enterprise", "Team Capacity Planning"),
    ("KNOWLEDGE", "Enterprise", "Internal Knowledge Library"),
    ("FACILITIES", "Enterprise", "Office Facilities Tracking"),
    ("FINANCE", "Enterprise", "Budget Planning"),
)


def build_registry(as_of: date) -> tuple[dict, list[dict]]:
    """Same date gives identical records; identities remain stable across dates."""
    created_at = datetime.combine(as_of, time.min, ZoneInfo(DEMO_TIMEZONE)).astimezone(timezone.utc)
    org = dict(
        id=uuid5(NAMESPACE, "northstar-biopharma-demo"), slug="northstar-biopharma-demo",
        display_name="Northstar Biopharma (fictional)", timezone=DEMO_TIMEZONE,
        created_at=created_at, updated_at=created_at,
    )
    applications = []
    lifecycle_pairs = (
        ("Operational", "Validated"), ("Operational", "Validated"),
        ("Implementation", "In Validation"), ("Implementation", "Validation Required"),
        ("Operational", "Remediation Required"), ("Retirement", "Validated"),
        ("Retired", "Validated"),
    )
    for number, (code, system_type, name) in enumerate(CATALOG, start=1):
        ci_id = f"NSB-{code}-{number:03d}"
        lifecycle, validation = lifecycle_pairs[(number - 8) % len(lifecycle_pairs)]
        non_gxp = system_type == "Enterprise"
        if number <= 7:
            lifecycle, validation = "Operational", "Validated"
        if non_gxp:
            validation = "Not Assessed"
        applications.append(dict(
            id=uuid5(NAMESPACE, ci_id), organization_id=org["id"], ci_id=ci_id,
            name=f"Northstar {name}", system_type=system_type,
            description=f"SYNTHETIC DEMO DATA — fictional {name.lower()} application. Source: {SEED_VERSION}.",
            gxp_classification="Non-GxP" if non_gxp else "GxP",
            criticality="Low" if non_gxp else "High" if number <= 7 else ("High", "Medium", "Low")[(number - 8) % 3],
            lifecycle_state=lifecycle, validation_state=validation,
            supplier="Northstar Demo Software (fictional)",
            platform=("Demo hosted platform", "Demo managed server", "Demo laboratory workstation")[(number - 1) % 3],
            created_at=created_at, updated_at=created_at,
        ))
    return org, applications


def export_registry(directory: Path, as_of: date) -> None:
    """Export generated fixtures; these are not an external-data import feed."""
    org, applications = build_registry(as_of)
    directory.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for filename, rows in (("organizations.csv", [org]), ("applications.csv", applications)):
        path = directory / filename
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[*rows[0], "source_system"], lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({**row, "source_system": "SYNTHETIC"})
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = dict(
        label="SYNTHETIC DEMO DATA", source_system="SYNTHETIC", seed_version=SEED_VERSION,
        as_of=as_of.isoformat(), timezone=DEMO_TIMEZONE, organizations=1, applications=len(applications),
        generator="backend/scripts/seed_demo.py", sha256=hashes,
        timestamp_meaning="Invented creation time at local midnight on as_of; not an actual historical event.",
    )
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_target(database_url: str, environment: str | None, confirmed: bool) -> URL:
    """Conservative guard against accidentally seeding the ordinary dev database."""
    if environment != "development" or not confirmed:
        raise ValueError("Apply requires ASSURGRID_ENV=development and --confirm-demo.")
    try:
        url = make_url(database_url)
    except (sa.exc.ArgumentError, ValueError):
        raise ValueError("Invalid database URL.") from None
    if url.drivername != "postgresql+psycopg" or url.database != "assurgrid_demo":
        raise ValueError("Apply requires a PostgreSQL database named assurgrid_demo.")
    # No libpq service/hostaddr overrides or multi-host query strings.
    socket = url.query.get("host")
    local_socket = isinstance(socket, str) and socket.startswith("/") and "," not in socket
    if set(url.query) - {"host", "connect_timeout"}:
        raise ValueError("Only host (local Unix socket) and connect_timeout URL options are allowed.")
    if socket is not None:
        if not local_socket or url.host is not None:
            raise ValueError("Apply requires a local Unix socket or a loopback host.")
    elif url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Apply requires a local Unix socket or a loopback host.")
    return url


def seed_registry(connection: Connection, as_of: date) -> dict[str, int]:
    """Caller owns the transaction. Never update/delete a row or erase history."""
    # Serialize registry writes while comparing existing records and adding missing ones.
    connection.execute(sa.text("LOCK TABLE organization, regulated_application IN SHARE ROW EXCLUSIVE MODE"))
    org, applications = build_registry(as_of)
    expected = ((organization, [org]), (regulated_application, applications))
    missing = []
    for table, rows in expected:
        by_id = {row["id"]: row for row in rows}
        existing = connection.execute(sa.select(table)).mappings().all()
        for row in existing:
            if row["id"] not in by_id or dict(row) != by_id[row["id"]]:
                raise ValueError("Database contains non-seed or changed records; no data was overwritten. Use the original --as-of or a fresh empty demo database.")
        existing_ids = {row["id"] for row in existing}
        missing.append((table, [row for row in rows if row["id"] not in existing_ids]))
    inserted = {}
    for table, rows in missing:
        if rows:
            connection.execute(table.insert(), rows)
        inserted[table.name] = len(rows)
    return inserted
