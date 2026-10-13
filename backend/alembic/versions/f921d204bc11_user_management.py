"""User administration and independently revocable organization access."""

from alembic import op
import sqlalchemy as sa

revision = "f921d204bc11"
down_revision = "e840c1328abc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "is_platform_admin", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "users", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "memberships",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("users", "is_platform_admin", server_default=None)
    op.alter_column("users", "version", server_default=None)
    op.alter_column("memberships", "enabled", server_default=None)


def downgrade():
    op.drop_column("memberships", "enabled")
    op.drop_column("users", "version")
    op.drop_column("users", "is_platform_admin")
