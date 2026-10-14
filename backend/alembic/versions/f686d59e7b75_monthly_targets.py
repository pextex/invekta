"""Monthly salesperson targets and business types, portable across MySQL/PostgreSQL."""
from alembic import op
import sqlalchemy as sa
revision = "f686d59e7b75"
down_revision = "e575c48d6a64"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("opportunities", sa.Column("business_type", sa.String(30), nullable=True))
    op.add_column("opportunity_stage_changes", sa.Column("business_type", sa.String(30), nullable=True))
    units = sa.table("business_units", sa.column("id", sa.Integer()), sa.column("code", sa.String()))
    for code, category in (("LUU", "sale"), ("INVEKTA", "contracted")):
        for name in ("opportunities", "opportunity_stage_changes"):
            table = sa.table(name, sa.column("business_unit_id", sa.Integer()), sa.column("business_type", sa.String()))
            op.get_bind().execute(table.update().where(table.c.business_unit_id.in_(sa.select(units.c.id).where(units.c.code == code))).values(business_type=category))
    op.create_table("monthly_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_unit_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["user_id", "business_unit_id"], ["memberships.user_id", "memberships.business_unit_id"], name="target_user_unit_fk"),
        sa.UniqueConstraint("business_unit_id", "user_id", "period", "category", name="unique_monthly_target"),
        sa.CheckConstraint("target_amount >= 0", name="nonnegative_target"),
        sa.CheckConstraint("version >= 1", name="positive_target_version"),
    )


def downgrade():
    op.drop_table("monthly_targets")
    op.drop_column("opportunity_stage_changes", "business_type")
    op.drop_column("opportunities", "business_type")
