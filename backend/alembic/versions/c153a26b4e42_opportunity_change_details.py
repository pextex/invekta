"""Record pipeline edits and the opportunity amount at the time of a change."""
from alembic import op
import sqlalchemy as sa
revision = "c153a26b4e42"
down_revision = "b042c15a9d31"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("opportunity_stage_changes", sa.Column("changes", sa.JSON(), nullable=True))
    op.add_column("opportunity_stage_changes", sa.Column("amount", sa.Numeric(14, 2), nullable=True))
    op.create_index("ix_stage_change_unit_time", "opportunity_stage_changes", ["business_unit_id", "changed_at"])

def downgrade():
    op.drop_index("ix_stage_change_unit_time", table_name="opportunity_stage_changes")
    op.drop_column("opportunity_stage_changes", "amount")
    op.drop_column("opportunity_stage_changes", "changes")
