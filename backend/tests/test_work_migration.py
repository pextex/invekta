"""Downgrade must refuse to drop populated work tables (isolated schema only)."""

import os
import subprocess
import sys
from uuid import uuid4
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


def test_populated_work_downgrade_preserves_records():
    target = make_url(os.environ["CRM_TEST_DATABASE_URL"])
    assert target.database.endswith("_test")
    schema = "work_migration_" + uuid4().hex
    raw = target.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(raw, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    isolated = target.update_query_dict({"options": f"-csearch_path={schema}"})
    env = {**os.environ, "DATABASE_URL": isolated.render_as_string(hide_password=False)}
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=env,
            check=True,
            capture_output=True,
        )
        with psycopg.connect(
            isolated.set(drivername="postgresql").render_as_string(hide_password=False),
            autocommit=True,
        ) as db:
            db.execute(
                "INSERT INTO users(id,username,name,password_hash,active,is_platform_admin,version) VALUES(1,'work-test','Test','unusable',true,false,1)"
            )
            db.execute(
                "INSERT INTO memberships(user_id,business_unit_id,role,enabled) VALUES(1,1,'manager',true)"
            )
            db.execute(
                "INSERT INTO companies(id,business_unit_id,owner_id,name,city,sector,stage,potential_value,is_demo) VALUES(1,1,1,'Preserved company','Test','Test','Kontakt',123.45,false)"
            )
            db.execute(
                "INSERT INTO tasks(business_unit_id,company_id,assignee_id,creator_id,title,due_at) VALUES(1,1,1,1,'Preserved task',now())"
            )
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "a162bced9031"],
            env=env,
            capture_output=True,
        )
        assert result.returncode != 0
        with psycopg.connect(
            isolated.set(drivername="postgresql").render_as_string(hide_password=False),
            autocommit=True,
        ) as db:
            assert (
                db.execute("SELECT title FROM tasks").fetchone()[0] == "Preserved task"
            )
            assert (
                db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
                == "b273e4f50612"
            )
    finally:
        with psycopg.connect(raw, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
