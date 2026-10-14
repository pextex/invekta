"""Track one-time activation state for the initial platform administrator."""

from alembic import op
import sqlalchemy as sa

revision = "f7c9bd318a42"
down_revision = "a162bced9031"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "bootstrap_pending",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column("users", "bootstrap_pending")
