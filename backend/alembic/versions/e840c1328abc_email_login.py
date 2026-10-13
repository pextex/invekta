"""Add unique email identifiers without changing existing users."""

from alembic import op
import sqlalchemy as sa

revision = "e840c1328abc"
down_revision = "c31e804d5b20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email", sa.String(254), nullable=True))
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.alter_column(
        "login_attempts", "username", type_=sa.String(254), existing_type=sa.String(100)
    )


def downgrade():
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "email")
