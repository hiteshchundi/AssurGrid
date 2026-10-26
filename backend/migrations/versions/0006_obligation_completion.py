"""Append-only completion evidence for scheduled obligations."""
from alembic import op
import sqlalchemy as sa

revision = "0006_obligation_completion"
down_revision = "0005_obligation_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_obligation_org_id", "governance_obligation", ["organization_id", "id"])
    op.create_table(
        "obligation_completion",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid, nullable=False),
        sa.Column("obligation_id", sa.Uuid, nullable=False),
        sa.Column("completed_by_id", sa.Uuid, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        sa.Column("notes", sa.String(2000), nullable=False),
        sa.ForeignKeyConstraint(["organization_id", "obligation_id"], ["governance_obligation.organization_id", "governance_obligation.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "completed_by_id"], ["membership.organization_id", "membership.user_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("obligation_id", name="uq_completion_obligation"),
        sa.CheckConstraint("evidence_reference ~ '[^[:space:]]'", name="ck_completion_evidence"),
        sa.CheckConstraint("notes ~ '[^[:space:]]'", name="ck_completion_notes"),
    )


def downgrade():
    op.drop_table("obligation_completion")
    op.drop_constraint("uq_obligation_org_id", "governance_obligation", type_="unique")
