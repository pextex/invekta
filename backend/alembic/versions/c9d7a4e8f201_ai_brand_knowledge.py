"""Approved brand knowledge for Invekta AI; portable, additive storage only."""
from alembic import op
import sqlalchemy as sa

revision = "c9d7a4e8f201"
down_revision = "b8a6c2d1e409"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_brand_knowledge",
        sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id"), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("ai_brand_knowledge")
