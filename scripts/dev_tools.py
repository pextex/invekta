"""Install missing uv privately, without changing system Python or CRM data."""

from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".dev-tools"
UV_VERSION = "0.12.23"


def ensure_uv():
    installed = shutil.which("uv")
    if installed:
        return installed
    binary = TOOLS / "bin/uv"
    if binary.is_file():
        return str(binary)
    print("Nedostaje uv; pripremam lokalni razvojni alat u .dev-tools (bez izmene sistemskog Python-a).", flush=True)
    try:
        subprocess.run([sys.executable, "-m", "venv", str(TOOLS)], check=True)
        subprocess.run(
            [str(TOOLS / "bin/python"), "-m", "pip", "install", "--disable-pip-version-check", f"uv=={UV_VERSION}"],
            check=True,
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Lokalna instalacija uv nije uspela; proverite prethodnu grešku i mrežu. "
            "Ako nedostaje venv/ensurepip, kontejner mora imati python3-venv. "
            "U recovery režimu otvorite Codespaces: View Creation Log, zatim Rebuild Container. "
            "CRM konfiguracija i baza nisu menjane."
        ) from None
    return str(binary)


def check_runtime():
    missing = [tool for tool in ("npm", "docker") if not shutil.which(tool)]
    if missing:
        raise RuntimeError(
            "Nedostaju razvojni alati: " + ", ".join(missing) + ". "
            "U recovery režimu instalacija uv sama nije dovoljna. Otvorite "
            "Codespaces: View Creation Log, zatim Codespaces: Rebuild Container. "
            "Nemojte brisati Codespace ili volume baze."
        )
    for command in (["docker", "info", "--format", "{{.ServerVersion}}"], ["docker", "compose", "version"]):
        try:
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Docker ne odgovara. Proverite Codespaces Creation Log i obnovite kontejner bez brisanja podataka.") from None
        if result.returncode:
            raise RuntimeError(
                "Docker daemon ili Compose nije dostupan. Instalacija uv ne rešava recovery kontejner. "
                "Otvorite Codespaces: View Creation Log, pa Codespaces: Rebuild Container; "
                "ne brišite Codespace ili volume baze."
            )


if __name__ == "__main__":
    try:
        ensure_uv()
        print("uv je spreman za python scripts/dev.py.", flush=True)
    except RuntimeError as error:
        sys.exit(str(error))
