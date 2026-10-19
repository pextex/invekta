"""Personal contact phone for CRM users."""
from alembic import op
import sqlalchemy as sa

revision = "ab27d6e901f3"
down_revision = "c9d7a4e8f201"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("phone", sa.String(40), nullable=True))


def downgrade():
    op.drop_column("users", "phone")
