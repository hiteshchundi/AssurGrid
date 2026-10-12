"""Add prototype identity storage; authentication follows separately."""

from alembic import op
import sqlalchemy as sa

revision = "0003_identity"
down_revision = "0002_application_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_application_organization_id", "regulated_application", ["organization_id", "id"])

    op.create_table(
        "user_account",
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

    op.create_table(
        "membership",
        sa.Column("organization_id", sa.Uuid, sa.ForeignKey("organization.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("user_id", sa.Uuid, sa.ForeignKey("user_account.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('Admin', 'Quality', 'Application Owner', 'Viewer')", name="ck_membership_role"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_membership_timestamps"),
    )

    op.create_table(
        "application_access",
        sa.Column("organization_id", sa.Uuid, primary_key=True),
        sa.Column("user_id", sa.Uuid, primary_key=True),
        sa.Column("application_id", sa.Uuid, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id", "user_id"], ["membership.organization_id", "membership.user_id"], name="fk_access_membership", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "application_id"], ["regulated_application.organization_id", "regulated_application.id"], name="fk_access_application", ondelete="RESTRICT"),
    )

    op.create_table(
        "browser_session",
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


def downgrade() -> None:
    # Only identity data is removed; registry rows are preserved.
    op.drop_table("browser_session")
    op.drop_table("application_access")
    op.drop_table("membership")
    op.drop_table("user_account")
    op.drop_constraint("uq_application_organization_id", "regulated_application", type_="unique")
