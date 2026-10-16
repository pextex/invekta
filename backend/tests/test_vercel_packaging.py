"""Exercise template generation with the sibling shared directory absent at runtime."""
import os
from pathlib import Path
import shutil
import subprocess
import sys


def test_separate_python_service_keeps_shared_templates(tmp_path):
    root = Path(__file__).resolve().parents[2]
    service = tmp_path / "backend"
    shutil.copytree(root / "backend/app", service / "app", ignore=shutil.ignore_patterns(
        "__pycache__", "static", "_vercel_data",
    ))
    shutil.copyfile(root / "backend/build_vercel.py", service / "build_vercel.py")
    shared = tmp_path / "shared"
    shared.mkdir()
    shutil.copyfile(root / "shared/message_catalog.json", shared / "message_catalog.json")
    # No DB configuration is needed for the packaging build or template generation.
    env = {"PATH": os.environ["PATH"]}
    subprocess.run([sys.executable, "build_vercel.py"], cwd=service, env=env, check=True, capture_output=True)
    assert (service / "app/_vercel_data/message_catalog.json").read_bytes() == (
        shared / "message_catalog.json"
    ).read_bytes()
    shutil.rmtree(shared)
    subprocess.run([sys.executable, "-c", '''
from app.message_templates import generate
draft = generate({"company": {"name": "Provera"}, "sender": {"name": "Prodavac", "organization": "INVEKTA"}, "mode": "email", "goal": "meeting"})
assert draft.subject and draft.body.startswith("Poštovani,")
assert "INVEKTA" in draft.body and "Prodavac" in draft.body
'''], cwd=service, env=env, check=True, capture_output=True)
