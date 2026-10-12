"""Add organization-scoped controls and dated policy versions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ExcludeConstraint

revision = "0004_policy_schema"
down_revision = "0003_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # UUID equality in the GiST exclusion constraint needs the standard extension.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "control_definition",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid, sa.ForeignKey("organization.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("control_key", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "id", name="uq_control_organization_id"),
        sa.UniqueConstraint("organization_id", "control_key", name="uq_control_organization_key"),
        sa.CheckConstraint("control_key ~ '^[A-Z][A-Z0-9_]*$'", name="ck_control_key"),
        sa.CheckConstraint("name ~ '[^[:space:]]'", name="ck_control_name"),
    )

    op.create_table(
        "governance_policy",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid, sa.ForeignKey("organization.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("policy_key", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "id", name="uq_policy_organization_id"),
        sa.UniqueConstraint("organization_id", "policy_key", name="uq_policy_organization_key"),
        sa.CheckConstraint("policy_key ~ '^[A-Z][A-Z0-9_]*$'", name="ck_policy_key"),
        sa.CheckConstraint("name ~ '[^[:space:]]'", name="ck_policy_name"),
    )

    op.create_table(
        "policy_version",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid, nullable=False),
        sa.Column("policy_id", sa.Uuid, nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("gxp_classification", sa.String(20), nullable=False),
        sa.Column("criticality", sa.String(20), nullable=False),
        sa.Column("change_reason", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id", "policy_id"], ["governance_policy.organization_id", "governance_policy.id"], name="fk_version_policy", ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "id", name="uq_version_organization_id"),
        sa.UniqueConstraint("policy_id", "version_number", name="uq_policy_version_number"),
        sa.CheckConstraint("version_number > 0", name="ck_policy_version_number"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_policy_version_period"),
        sa.CheckConstraint("gxp_classification IN ('GxP', 'Non-GxP')", name="ck_policy_version_gxp"),
        sa.CheckConstraint("criticality IN ('High', 'Medium', 'Low')", name="ck_policy_version_criticality"),
        sa.CheckConstraint("change_reason ~ '[^[:space:]]'", name="ck_policy_version_reason"),
        ExcludeConstraint(("policy_id", "="), (sa.text("daterange(effective_from, effective_to, '[)')"), "&&"), using="gist", name="ex_policy_version_period"),
    )

    op.create_table(
        "policy_control_rule",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid, nullable=False),
        sa.Column("policy_version_id", sa.Uuid, nullable=False),
        sa.Column("control_definition_id", sa.Uuid, nullable=False),
        sa.Column("frequency_months", sa.Integer, nullable=False),
        sa.Column("due_soon_days", sa.Integer, nullable=False),
        sa.Column("mandatory", sa.Boolean, nullable=False),
        sa.Column("evidence_requirement", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id", "policy_version_id"], ["policy_version.organization_id", "policy_version.id"], name="fk_rule_version", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "control_definition_id"], ["control_definition.organization_id", "control_definition.id"], name="fk_rule_control", ondelete="RESTRICT"),
        sa.UniqueConstraint("policy_version_id", "control_definition_id", name="uq_rule_version_control"),
        sa.CheckConstraint("frequency_months > 0", name="ck_rule_frequency"),
        sa.CheckConstraint("due_soon_days >= 0", name="ck_rule_due_soon"),
        sa.CheckConstraint("evidence_requirement IS NULL OR evidence_requirement ~ '[^[:space:]]'", name="ck_rule_evidence"),
    )


def downgrade() -> None:
    op.drop_table("policy_control_rule")
    op.drop_table("policy_version")
    op.drop_table("governance_policy")
    op.drop_table("control_definition")
    # Keep btree_gist: it may predate this migration or serve other schemas.
