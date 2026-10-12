"""SQLAlchemy Core table definitions; business rules remain in domain services."""

import sqlalchemy as sa

metadata = sa.MetaData()

organization = sa.Table(
    "organization",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("slug", sa.String(80), nullable=False),
    sa.Column("display_name", sa.String(200), nullable=False),
    sa.Column("timezone", sa.String(100), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("slug", name="uq_organization_slug"),
    sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="ck_organization_slug"),
    sa.CheckConstraint("display_name ~ '[^[:space:]]'", name="ck_organization_display_name"),
    sa.CheckConstraint("timezone ~ '[^[:space:]]'", name="ck_organization_timezone"),
    sa.CheckConstraint("updated_at >= created_at", name="ck_organization_timestamps"),
)

regulated_application = sa.Table(
    "regulated_application",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("organization_id", sa.Uuid, sa.ForeignKey("organization.id", ondelete="RESTRICT"), nullable=False),
    sa.Column("ci_id", sa.String(100), nullable=False),
    sa.Column("name", sa.String(200), nullable=False),
    sa.Column("system_type", sa.String(100), nullable=False),
    sa.Column("description", sa.Text, nullable=True),
    sa.Column("gxp_classification", sa.String(20), nullable=False),
    sa.Column("criticality", sa.String(20), nullable=False),
    sa.Column("lifecycle_state", sa.String(30), nullable=False),
    sa.Column("validation_state", sa.String(30), nullable=False),
    sa.Column("supplier", sa.String(200), nullable=True),
    sa.Column("platform", sa.String(200), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("organization_id", "ci_id", name="uq_application_organization_ci"),
    sa.CheckConstraint("ci_id ~ '^[^[:space:]]+$'", name="ck_application_ci_id"),
    sa.CheckConstraint("name ~ '[^[:space:]]'", name="ck_application_name"),
    sa.CheckConstraint("system_type ~ '[^[:space:]]'", name="ck_application_system_type"),
    sa.CheckConstraint("gxp_classification IN ('GxP', 'Non-GxP')", name="ck_application_gxp"),
    sa.CheckConstraint("criticality IN ('High', 'Medium', 'Low')", name="ck_application_criticality"),
    sa.CheckConstraint(
        "lifecycle_state IN ('Implementation', 'Operational', 'Retirement', 'Retired')",
        name="ck_application_lifecycle",
    ),
    sa.CheckConstraint(
        "validation_state IN ('Not Assessed', 'Validation Required', 'In Validation', 'Validated', 'Remediation Required')",
        name="ck_application_validation",
    ),
    sa.CheckConstraint("updated_at >= created_at", name="ck_application_timestamps"),
)
