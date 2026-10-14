"""Add a company-scoped task calendar using portable SQL types."""
from alembic import op
import sqlalchemy as sa
revision = "d264b37c5f53"
down_revision = "c153a26b4e42"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id"), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("due_time", sa.Time(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["owner_id", "business_unit_id"], ["memberships.user_id", "memberships.business_unit_id"], name="task_owner_unit_fk"),
        sa.ForeignKeyConstraint(["company_id", "business_unit_id"], ["companies.id", "companies.business_unit_id"], name="task_company_unit_fk"),
        sa.CheckConstraint("status IN ('planned', 'done')", name="valid_task_status"),
        sa.CheckConstraint("version >= 1", name="positive_task_version"),
    )
    op.create_index("ix_task_unit_date_owner", "tasks", ["business_unit_id", "due_date", "owner_id"])

def downgrade():
    op.drop_index("ix_task_unit_date_owner", table_name="tasks")
    op.drop_table("tasks")
