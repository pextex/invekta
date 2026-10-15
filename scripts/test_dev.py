"""Safety checks for the development launcher; no database connections."""

import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from dev import preview_origin
from dev_tools import ensure_uv, check_runtime
from dev_database import check_schema, local_url
from init_dev_database import initialize_empty_database
from sqlalchemy.engine import make_url
from app.config import get_settings


class DevelopmentSafetyTests(unittest.TestCase):
    def test_initialization_rejects_existing_objects_even_without_alembic_revision(self):
        for schema, method in (("public", "get_table_names"), ("other", "get_view_names"),
                               ("public", "get_materialized_view_names"), ("other", "get_sequence_names")):
            with self.subTest(schema=schema, method=method), \
                    patch("init_dev_database.local_url", return_value=make_url("postgresql+psycopg://localhost/crm_test")), \
                    patch("init_dev_database.create_engine"), \
                    patch("init_dev_database.inspect") as inspect, \
                    patch("init_dev_database.subprocess.run") as run:
                inspector = inspect.return_value
                inspector.get_schema_names.return_value = [schema]
                for name in ("get_table_names", "get_view_names", "get_materialized_view_names", "get_sequence_names"):
                    getattr(inspector, name).return_value = []
                getattr(inspector, method).return_value = ["existing_object"]
                with self.assertRaisesRegex(RuntimeError, "Baza nije prazna"):
                    initialize_empty_database()
                run.assert_not_called()

    def test_explicit_initialization_runs_upgrade_only_when_empty(self):
        with patch("init_dev_database.local_url", return_value=make_url("postgresql+psycopg://localhost/crm_test")), \
                patch("init_dev_database.create_engine"), \
                patch("init_dev_database.inspect") as inspect, \
                patch("init_dev_database.subprocess.run") as run:
            inspector = inspect.return_value
            inspector.get_schema_names.return_value = ["pg_catalog", "information_schema", "public"]
            for name in ("get_table_names", "get_view_names", "get_materialized_view_names", "get_sequence_names"):
                getattr(inspector, name).return_value = []
            initialize_empty_database()
            run.assert_called_once()
            self.assertEqual(run.call_args.args[0][-3:], ["alembic", "upgrade", "head"])

    def test_missing_uv_is_installed_privately_and_reused_without_path_change(self):
        with TemporaryDirectory() as directory, \
                patch("dev_tools.TOOLS", Path(directory)), \
                patch("dev_tools.shutil.which", return_value=None), \
                patch("dev_tools.subprocess.run") as run:
            binary = Path(directory) / "bin/uv"
            self.assertEqual(ensure_uv(), str(binary))
            self.assertEqual(run.call_args_list[0].args[0][-2:], ["venv", directory])
            self.assertEqual(run.call_args_list[1].args[0][-1], "uv==0.12.23")
            self.assertNotIn("--user", run.call_args_list[1].args[0])
            binary.parent.mkdir()
            binary.touch()
            run.reset_mock()
            self.assertEqual(ensure_uv(), str(binary))
            run.assert_not_called()

    def test_recovery_without_docker_stops_before_installing_or_starting_services(self):
        with patch("dev_tools.shutil.which", return_value=None), \
                patch("dev_tools.subprocess.run") as run:
            with self.assertRaisesRegex(RuntimeError, "View Creation Log"):
                check_runtime()
            run.assert_not_called()
        with patch("dev_tools.shutil.which", return_value="available"), \
                patch("dev_tools.subprocess.run") as run:
            run.return_value.returncode = 1
            with self.assertRaisesRegex(RuntimeError, "Docker daemon"):
                check_runtime()

    def test_failed_uv_install_reports_error_without_starting_crm(self):
        with TemporaryDirectory() as directory, \
                patch("dev_tools.TOOLS", Path(directory)), \
                patch("dev_tools.shutil.which", return_value=None), \
                patch("dev_tools.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["venv"])):
            with self.assertRaisesRegex(RuntimeError, "baza nisu menjane"):
                ensure_uv()

    def test_exact_codespaces_https_origin(self):
        self.assertEqual(preview_origin({"CODESPACE_NAME": "test-space-123"}),
                         "https://test-space-123-5173.app.github.dev")
        self.assertEqual(preview_origin({}), "http://localhost:5173")
        with self.assertRaises(RuntimeError):
            preview_origin({"CODESPACE_NAME": "bad/name"})

    def test_rejects_remote_and_non_postgres_before_connection(self):
        for url in (
            "mysql+pymysql://localhost/crm",
            "postgresql+psycopg://database.example/crm",
            "postgresql+psycopg://127.0.0.1:6432/crm",
            "postgresql+psycopg://127.0.0.1/",
            "invalid-url",
        ):
            with self.subTest(url=url), patch.dict(os.environ, DATABASE_URL=url):
                get_settings.cache_clear()
                with self.assertRaises(RuntimeError) as error:
                    local_url()
                self.assertNotIn(url, str(error.exception))
        get_settings.cache_clear()

    def test_accepts_local_postgres(self):
        with patch.dict(os.environ, DATABASE_URL="postgresql+psycopg://localhost:5432/crm_test"):
            get_settings.cache_clear()
            self.assertEqual(local_url().database, "crm_test")
        get_settings.cache_clear()


    def test_outdated_or_empty_schema_stops_without_upgrade(self):
        for current in (("previous",), ()):
            with self.subTest(current=current), \
                    patch("dev_database.create_engine") as create_engine, \
                    patch("dev_database.MigrationContext") as context, \
                    patch("dev_database.ScriptDirectory") as scripts, \
                    patch("alembic.command.upgrade") as upgrade:
                connection = create_engine.return_value.connect.return_value.__enter__.return_value
                context.configure.return_value.get_current_heads.return_value = current
                script = scripts.from_config.return_value
                script.get_heads.return_value = ["required"]
                revision = MagicMock(revision="required", doc="Required schema change")
                script.iterate_revisions.return_value = [revision]
                output = StringIO()
                with redirect_stdout(output), self.assertRaises(RuntimeError):
                    check_schema("postgresql+psycopg://localhost/crm_test")
                self.assertIn("required: Required schema change", output.getvalue())
                upgrade.assert_not_called()
                connection.exec_driver_sql.assert_called_once_with("SET TRANSACTION READ ONLY")
                create_engine.return_value.dispose.assert_called_once()


if __name__ == "__main__":
    unittest.main()
