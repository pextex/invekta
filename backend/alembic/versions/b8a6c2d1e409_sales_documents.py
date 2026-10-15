"""Private brand sales documents with portable PostgreSQL/MySQL binary storage."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import MEDIUMBLOB

revision = "b8a6c2d1e409"
down_revision = "a797e60f8c86"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sales_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_unit_id", sa.Integer(), sa.ForeignKey("business_units.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary().with_variant(MEDIUMBLOB(), "mysql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_id", "business_unit_id"],
                                ["memberships.user_id", "memberships.business_unit_id"], name="document_uploader_unit_fk"),
        sa.CheckConstraint("size_bytes > 0 AND size_bytes <= 10485760", name="valid_sales_document_size"),
    )
    op.create_index("ix_sales_document_unit_created", "sales_documents", ["business_unit_id", "created_at"])


def downgrade():
    op.drop_index("ix_sales_document_unit_created", table_name="sales_documents")
    op.drop_table("sales_documents")
