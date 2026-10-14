"""Company address and Serbian tax identifier; preserve existing companies."""
from alembic import op
import sqlalchemy as sa
revision = "b042c15a9d31"
down_revision = "a162bced9031"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("companies", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("companies", sa.Column("pib", sa.String(9), nullable=True))

def downgrade():
    op.drop_column("companies", "pib")
    op.drop_column("companies", "address")
