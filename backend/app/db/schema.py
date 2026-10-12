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
    sa.UniqueConstraint("organization_id", "id", name="uq_application_organization_id"),
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


user_account = sa.Table(
    "user_account", metadata,
    sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("email", sa.String(254), nullable=False),
    sa.Column("display_name", sa.String(200), nullable=False),
    sa.Column("password_hash", sa.Text, nullable=False),
    sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("email", name="uq_user_account_email"),
    sa.CheckConstraint("email = lower(email) AND email ~ '^[^[:space:]@]+@[^[:space:]@]+$'", name="ck_user_account_email"),
    sa.CheckConstraint("display_name ~ '[^[:space:]]'", name="ck_user_account_display_name"),
    sa.CheckConstraint("password_hash ~ '[^[:space:]]'", name="ck_user_account_password_hash"),
    sa.CheckConstraint("updated_at >= created_at", name="ck_user_account_timestamps"),
)

membership = sa.Table(
    "membership", metadata,
    sa.Column("organization_id", sa.Uuid, sa.ForeignKey("organization.id", ondelete="RESTRICT"), primary_key=True),
    sa.Column("user_id", sa.Uuid, sa.ForeignKey("user_account.id", ondelete="RESTRICT"), primary_key=True),
    sa.Column("role", sa.String(30), nullable=False),
    sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.CheckConstraint("role IN ('Admin', 'Quality', 'Application Owner', 'Viewer')", name="ck_membership_role"),
    sa.CheckConstraint("updated_at >= created_at", name="ck_membership_timestamps"),
)

application_access = sa.Table(
    "application_access", metadata,
    sa.Column("organization_id", sa.Uuid, primary_key=True),
    sa.Column("user_id", sa.Uuid, primary_key=True),
    sa.Column("application_id", sa.Uuid, primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.ForeignKeyConstraint(["organization_id", "user_id"], ["membership.organization_id", "membership.user_id"], name="fk_access_membership", ondelete="RESTRICT"),
    sa.ForeignKeyConstraint(["organization_id", "application_id"], ["regulated_application.organization_id", "regulated_application.id"], name="fk_access_application", ondelete="RESTRICT"),
)

browser_session = sa.Table(
    "browser_session", metadata,
    sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("organization_id", sa.Uuid, nullable=False),
    sa.Column("user_id", sa.Uuid, nullable=False),
    sa.Column("token_hash", sa.String(64), nullable=False),
    sa.Column("csrf_token_hash", sa.String(64), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(["organization_id", "user_id"], ["membership.organization_id", "membership.user_id"], name="fk_session_membership", ondelete="RESTRICT"),
    sa.UniqueConstraint("token_hash", name="uq_session_token_hash"),
    sa.CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="ck_session_token_hash"),
    sa.CheckConstraint("csrf_token_hash ~ '^[0-9a-f]{64}$'", name="ck_session_csrf_hash"),
    sa.CheckConstraint("expires_at > created_at", name="ck_session_expiry"),
    sa.CheckConstraint("revoked_at IS NULL OR revoked_at >= created_at", name="ck_session_revocation"),
)
