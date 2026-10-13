"""Private AI draft storage and generation budget."""

from alembic import op
import sqlalchemy as sa

revision = "a162bced9031"
down_revision = "f921d204bc11"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_unit_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("recipient", sa.String(254)),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "business_unit_id"],
            ["companies.id", "companies.business_unit_id"],
        ),
        sa.ForeignKeyConstraint(
            ["actor_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        sa.CheckConstraint("version >= 1", name="positive_ai_draft_version"),
    )
    op.create_index(
        "ix_ai_draft_actor_unit", "ai_drafts", ["actor_id", "business_unit_id"]
    )
    op.create_table(
        "ai_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_ai_attempt_actor_time", "ai_attempts", ["actor_id", "created_at"]
    )


def downgrade():
    op.drop_table("ai_attempts")
    op.drop_table("ai_drafts")
