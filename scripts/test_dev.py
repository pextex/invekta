"""Safety checks for the development launcher; no database connections."""

import os
from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import MagicMock, patch

from dev import preview_origin
from dev_database import check_schema, local_url
from app.config import get_settings


class DevelopmentSafetyTests(unittest.TestCase):
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
