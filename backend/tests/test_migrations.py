"""Exercise upgrade and downgrade in an isolated schema of the test database."""

import os
import subprocess
import sys
from decimal import Decimal
from uuid import uuid4
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


def test_legacy_estimates_migrate_once_without_losing_company_data():
    target = make_url(os.environ["CRM_TEST_DATABASE_URL"])
    assert target.database.endswith("_test")
    schema = "migration_" + uuid4().hex
    raw = target.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(raw, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    isolated = target.update_query_dict({"options": f"-csearch_path={schema}"})
    env = {**os.environ, "DATABASE_URL": isolated.render_as_string(hide_password=False)}

    def migrate(version, action="upgrade"):
        subprocess.run(
            [sys.executable, "-m", "alembic", action, version],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    try:
        migrate("08e422fba997")
        with psycopg.connect(
            isolated.set(drivername="postgresql").render_as_string(hide_password=False),
            autocommit=True,
        ) as connection:
            connection.execute(
                "INSERT INTO business_units(id,code,name) VALUES(1,'LUU','LUU')"
            )
            connection.execute(
                "INSERT INTO users(id,username,name,password_hash,active) VALUES(1,'migration-user','Test','unusable-test-hash',true)"
            )
            connection.execute(
                "INSERT INTO memberships(user_id,business_unit_id,role) VALUES(1,1,'manager')"
            )
            connection.execute(
                "INSERT INTO companies(id,business_unit_id,owner_id,name,city,sector,stage,potential_value,is_demo) VALUES(1,1,1,'Legacy demo','Beograd','Test','Kontakt',12345.67,true)"
            )
            connection.execute(
                "INSERT INTO companies(id,business_unit_id,owner_id,name,city,sector,stage,potential_value,is_demo) VALUES(2,1,1,%s,'Niš','Test','Pregovori',0.01,false)",
                ("L" * 200,),
            )
        migrate("head")
        migrate("head")
        with psycopg.connect(
            isolated.set(drivername="postgresql").render_as_string(hide_password=False),
            autocommit=True,
        ) as connection:
            rows = connection.execute(
                "SELECT company_id,business_unit_id,amount,stage,is_demo FROM opportunities ORDER BY company_id"
            ).fetchall()
            assert rows == [
                (1, 1, Decimal("12345.67"), "Kontaktiran", True),
                (2, 1, Decimal("0.01"), "Pregovori", False),
            ]
            assert (
                connection.execute(
                    "SELECT max(length(title)) FROM opportunities"
                ).fetchone()[0]
                == 200
            )
            assert connection.execute(
                "SELECT potential_value,stage FROM companies WHERE id=1"
            ).fetchone() == (Decimal("12345.67"), "Kontakt")
        migrate("08e422fba997", "downgrade")
        with psycopg.connect(
            isolated.set(drivername="postgresql").render_as_string(hide_password=False),
            autocommit=True,
        ) as connection:
            assert connection.execute(
                "SELECT name,potential_value FROM companies WHERE id=1"
            ).fetchone() == ("Legacy demo", Decimal("12345.67"))
    finally:
        with psycopg.connect(raw, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema))
            )
