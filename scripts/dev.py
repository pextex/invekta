"""Start the existing CRM in Codespaces or locally; never migrate or seed."""

import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def preview_origin(env):
    name = env.get("CODESPACE_NAME", "")
    domain = env.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    if not name:
        return "http://localhost:5173"
    if not re.fullmatch(r"[a-zA-Z0-9-]+", name) or not re.fullmatch(
        r"[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*", domain
    ):
        raise RuntimeError("Neispravna Codespaces adresa pregleda.")
    return f"https://{name}-5173.{domain}"


def check_ports():
    for port in (8000, 5173):
        with socket.socket() as sock:
            # A just-stopped HTTP server can leave TIME_WAIT sockets behind.
            # Reuse that address, but still reject an active listener.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
            except OSError:
                raise RuntimeError(f"Port {port} je zauzet. Zaustavite prethodni razvojni server.") from None


def run(args, cwd=ROOT, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def wait_ready(process, url):
    for _ in range(120):
        if process.poll() is not None:
            raise RuntimeError("Razvojni server se zaustavio; proverite prethodni ispis.")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Server nije spreman posle 60 sekundi.")


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def main():
    if os.name != "posix":
        raise RuntimeError("Ova komanda koristi Linux/macOS; na Windows-u koristite Codespaces ili WSL.")
    for tool in ("uv", "npm", "docker"):
        if not shutil.which(tool):
            raise RuntimeError(f"Nedostaje {tool}. Otvorite projekat pomoću .devcontainer konfiguracije.")
    check_ports()
    env = dict(os.environ)
    origin = preview_origin(env)
    env.update(
        CRM_ALLOWED_ORIGINS=origin + ",http://localhost:5173,http://127.0.0.1:5173",
        CRM_COOKIE_SECURE="true" if origin.startswith("https:") else "false",
        CRM_AI_ENABLED="false",
    )
    run([sys.executable, "scripts/setup_dev.py"], env=env)
    run(["uv", "sync", "--frozen"], cwd=ROOT / "backend", env=env)
    python = str(ROOT / "backend/.venv/bin/python")
    checker = str(ROOT / "scripts/dev_database.py")
    # Validate before Docker or any database connection, including inherited env vars.
    run([python, checker, "validate"], env=env)
    run(["docker", "compose", "up", "-d", "--wait", "db"], env=env)
    run([python, checker, "check"], env=env)
    run(["npm", "ci", "--no-audit", "--no-fund"], cwd=ROOT / "frontend", env=env)

    processes = []
    try:
        backend = subprocess.Popen(
            [python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
             "--port", "8000", "--reload", "--reload-dir", "app"],
            cwd=ROOT / "backend", env=env, start_new_session=True,
        )
        processes.append(backend)
        wait_ready(backend, "http://127.0.0.1:8000/api/ready")
        frontend = subprocess.Popen(
            ["npm", "run", "dev"], cwd=ROOT / "frontend", env=env,
            start_new_session=True,
        )
        processes.append(frontend)
        wait_ready(frontend, "http://127.0.0.1:5173/api/ready")
        print(f"\nCRM i baza su spremni: {origin}", flush=True)
        print("Codespaces: Ports → 5173 → Open in Browser (Private).", flush=True)
        print("Ctrl+C zaustavlja API i Vite; PostgreSQL i podaci ostaju sačuvani.\n", flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        raise RuntimeError("Jedan razvojni server se zaustavio; zaustavljam i drugi.")
    finally:
        for process in reversed(processes):
            stop(process)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        main()
    except KeyboardInterrupt:
        print("\nRazvojni serveri su zaustavljeni; baza je sačuvana.")
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
    except RuntimeError as error:
        sys.exit(str(error))
