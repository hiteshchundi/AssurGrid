"""Add policy-linked scheduled obligations without derived health state."""
from alembic import op
import sqlalchemy as sa

revision = "0005_obligation_schema"
down_revision = "0004_policy_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_rule_obligation_reference", "policy_control_rule", ["organization_id", "id", "policy_version_id", "control_definition_id"])

    op.create_table(
        "governance_obligation",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid, nullable=False),
        sa.Column("application_id", sa.Uuid, nullable=False),
        sa.Column("policy_control_rule_id", sa.Uuid, nullable=False),
        sa.Column("policy_version_id", sa.Uuid, nullable=False),
        sa.Column("control_definition_id", sa.Uuid, nullable=False),
        sa.Column("window_start", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("frequency_months", sa.Integer, nullable=False),
        sa.Column("due_soon_days", sa.Integer, nullable=False),
        sa.Column("mandatory", sa.Boolean, nullable=False),
        sa.Column("evidence_requirement", sa.Text, nullable=True),
        sa.Column("assigned_owner_id", sa.Uuid, nullable=True),
        sa.Column("generation_key", sa.String(64), nullable=False),
        sa.Column("superseded_by_id", sa.Uuid, nullable=True),
        sa.Column("supersession_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id", "application_id"], ["regulated_application.organization_id", "regulated_application.id"], name="fk_obligation_application", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "policy_control_rule_id", "policy_version_id", "control_definition_id"], ["policy_control_rule.organization_id", "policy_control_rule.id", "policy_control_rule.policy_version_id", "policy_control_rule.control_definition_id"], name="fk_obligation_rule", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "assigned_owner_id"], ["membership.organization_id", "membership.user_id"], name="fk_obligation_owner", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "superseded_by_id", "application_id", "control_definition_id"], ["governance_obligation.organization_id", "governance_obligation.id", "governance_obligation.application_id", "governance_obligation.control_definition_id"], name="fk_obligation_supersession", ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "id", "application_id", "control_definition_id", name="uq_obligation_supersession_target"),
        sa.UniqueConstraint("organization_id", "generation_key", name="uq_obligation_generation_key"),
        sa.UniqueConstraint("organization_id", "application_id", "policy_control_rule_id", "window_start", name="uq_obligation_rule_window"),
        sa.CheckConstraint("due_date >= window_start", name="ck_obligation_dates"),
        sa.CheckConstraint("frequency_months > 0", name="ck_obligation_frequency"),
        sa.CheckConstraint("due_soon_days >= 0", name="ck_obligation_due_soon"),
        sa.CheckConstraint("generation_key ~ '^[0-9a-f]{64}$'", name="ck_obligation_generation_key"),
        sa.CheckConstraint("evidence_requirement IS NULL OR evidence_requirement ~ '[^[:space:]]'", name="ck_obligation_evidence"),
        sa.CheckConstraint("(superseded_by_id IS NULL AND supersession_reason IS NULL) OR (superseded_by_id IS NOT NULL AND superseded_by_id <> id AND supersession_reason IS NOT NULL AND supersession_reason ~ '[^[:space:]]')", name="ck_obligation_supersession"),
    )


def downgrade() -> None:
    op.drop_table("governance_obligation")
    op.drop_constraint("uq_rule_obligation_reference", "policy_control_rule", type_="unique")
