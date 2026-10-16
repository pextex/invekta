"""Package the shared catalog inside the Python service; never access a database."""
from pathlib import Path
import json
import shutil


def main() -> None:
    backend = Path(__file__).resolve().parent
    source = backend.parent / "shared/message_catalog.json"
    # Fail the build if the repository's shared sources are unavailable or invalid.
    json.loads(source.read_text(encoding="utf-8"))
    destination = backend / "app/_vercel_data/message_catalog.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    print("Zajednički katalog je uključen u backend paket. Baza nije menjana.")


if __name__ == "__main__":
    main()
