"""Company contract dates and expiration reminders (no invented legacy dates)."""
from alembic import op
import sqlalchemy as sa
revision = 'de50a9b234c6'
down_revision = 'cd49f8a123b5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('companies', sa.Column('contract_signed_on', sa.Date(), nullable=True))
    op.add_column('companies', sa.Column('contract_expires_on', sa.Date(), nullable=True))
    op.create_check_constraint('valid_company_contract_dates', 'companies',
        'contract_signed_on IS NULL OR contract_expires_on IS NULL OR contract_expires_on >= contract_signed_on')
    op.create_index('ix_company_unit_contract_end', 'companies', ['business_unit_id', 'contract_expires_on'])


def downgrade():
    op.drop_index('ix_company_unit_contract_end', table_name='companies')
    op.drop_constraint('valid_company_contract_dates', 'companies', type_='check')
    op.drop_column('companies', 'contract_expires_on')
    op.drop_column('companies', 'contract_signed_on')
