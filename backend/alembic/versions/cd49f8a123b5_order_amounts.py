"""Order values and explicit realization dates for individual and collective targets."""
from alembic import op
import sqlalchemy as sa
revision='cd49f8a123b5'
down_revision='bc38e7f012a4'
branch_labels=None
depends_on=None

def upgrade():
    # Existing orders remain unpriced; never invent historical revenue or dates.
    op.add_column('marketing_orders',sa.Column('amount',sa.Numeric(14,2),nullable=True))
    op.add_column('marketing_orders',sa.Column('business_type',sa.String(30),nullable=True))
    op.add_column('marketing_orders',sa.Column('realized_at',sa.DateTime(timezone=True),nullable=True))
    op.create_check_constraint('positive_order_amount','marketing_orders','amount IS NULL OR amount > 0')

def downgrade():
    op.drop_constraint('positive_order_amount','marketing_orders',type_='check')
    op.drop_column('marketing_orders','realized_at')
    op.drop_column('marketing_orders','business_type')
    op.drop_column('marketing_orders','amount')
