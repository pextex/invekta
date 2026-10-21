"""Marketing role and owner-scoped order pipeline."""
from alembic import op
import sqlalchemy as sa
revision='bc38e7f012a4'
down_revision='ab27d6e901f3'
branch_labels=None
depends_on=None

def upgrade():
    op.drop_constraint('valid_membership_role','memberships',type_='check')
    op.create_check_constraint('valid_membership_role','memberships',"role IN ('sales','marketing','manager','admin')")
    op.create_table('marketing_orders',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('business_unit_id',sa.Integer(),sa.ForeignKey('business_units.id'),nullable=False),
        sa.Column('owner_id',sa.Integer(),nullable=False),
        sa.Column('first_name',sa.String(100),nullable=False),sa.Column('last_name',sa.String(100),nullable=False),
        sa.Column('phone',sa.String(40),nullable=False),sa.Column('email',sa.String(254),nullable=True),sa.Column('source',sa.String(20),nullable=False),
        sa.Column('status',sa.String(20),nullable=False,server_default='new'),
        sa.Column('version',sa.Integer(),nullable=False,server_default='1'),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id','business_unit_id'],['memberships.user_id','memberships.business_unit_id'],name='marketing_order_owner_fk'),
        sa.CheckConstraint("source IN ('website','phone')",name='valid_order_source'),
        sa.CheckConstraint("status IN ('new','proposal_sent','won','lost')",name='valid_order_status'),
        sa.CheckConstraint('version >= 1',name='positive_order_version'))
    op.create_index('ix_order_unit_owner_status','marketing_orders',['business_unit_id','owner_id','status'])

def downgrade():
    # Refuse a destructive downgrade while marketing accounts or orders exist.
    connection=op.get_bind()
    if connection.scalar(sa.text("SELECT COUNT(*) FROM memberships WHERE role='marketing'")) or connection.scalar(sa.text('SELECT COUNT(*) FROM marketing_orders')):
        raise RuntimeError('Downgrade zahteva prethodno eksplicitno rešavanje marketing naloga i porudžbina.')
    op.drop_table('marketing_orders')
    op.drop_constraint('valid_membership_role','memberships',type_='check')
    op.create_check_constraint('valid_membership_role','memberships',"role IN ('sales','manager','admin')")
