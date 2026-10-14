"""Register the three organizations without granting existing users access."""

from alembic import op
import sqlalchemy as sa

revision = "c31e804d5b20"
down_revision = "d79adb2eadaf"
branch_labels = None
depends_on = None

UNITS = [
    ("LUU", "LUU"),
    ("INVEKTA", "Invekta"),
    ("CENOBOTS", "Cenobots"),
]


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        # MySQL assigns the auto-increment IDs. The migration is idempotent for
        # partially imported databases and does not grant any memberships.
        for code, name in UNITS:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO business_units (code, name)
                    SELECT :code, :name
                    WHERE NOT EXISTS (
                        SELECT 1 FROM business_units WHERE code = :code
                    )
                    """
                ).bindparams(code=code, name=name)
            )
        return

    # PostgreSQL keeps the existing explicit-ID and sequence repair behavior.
    op.execute(sa.text("LOCK TABLE business_units IN SHARE ROW EXCLUSIVE MODE"))
    for code, name in UNITS:
        op.execute(
            sa.text(
                """
                INSERT INTO business_units(id, code, name)
                SELECT COALESCE(MAX(id), 0) + 1, :code, :name FROM business_units
                HAVING NOT EXISTS (SELECT 1 FROM business_units WHERE code = :code)
                ON CONFLICT (code) DO NOTHING
                """
            ).bindparams(code=code, name=name)
        )
    op.execute(
        sa.text(
            """
            SELECT setval(pg_get_serial_sequence('business_units', 'id'),
              GREATEST((SELECT MAX(id) FROM business_units),
                       (SELECT last_value FROM business_units_id_seq)), true)
            """
        )
    )


def downgrade():
    # Preserve organizations and any dependent business records; this is a
    # forward data registration, not permission to delete customer data.
    pass
