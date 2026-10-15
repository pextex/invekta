"""Monthly collective brand goal and informational team bonus."""
from alembic import op
import sqlalchemy as sa
revision = "a797e60f8c86"
down_revision = "f686d59e7b75"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("team_bonuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id"), nullable=False),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("reward_note", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("business_unit_id", "period", name="unique_team_bonus_period"),
        sa.CheckConstraint("target_amount >= 0", name="nonnegative_team_bonus_target"),
        sa.CheckConstraint("version >= 1", name="positive_team_bonus_version"),
    )

def downgrade():
    op.drop_table("team_bonuses")
