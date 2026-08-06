"""Importiert und veröffentlicht automatisch den nächsten fehlenden Spieltag."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from config import CURRENT_SEASON
from publish_changes import publish_generated_data


BACKEND_DIR = Path(__file__).resolve().parent
PUBLIC_FILE = BACKEND_DIR.parent / "docs" / "data" / f"{CURRENT_SEASON}.json"


def next_missing_matchday() -> int | None:
    payload = json.loads(PUBLIC_FILE.read_text(encoding="utf-8"))
    existing = {
        int(item["matchday"])
        for item in payload.get("matchdays", [])
    }
    return next((number for number in range(1, 35) if number not in existing), None)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importiert den nächsten fehlenden Spieltag mit Edge."
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Daten speichern, aber nicht committen und pushen.",
    )
    args = parser.parse_args()

    matchday = next_missing_matchday()
    if matchday is None:
        print(f"{CURRENT_SEASON} ist bereits vollständig.")
        return

    print(f"Automatischer Import: {CURRENT_SEASON}, Spieltag {matchday}")
    subprocess.run(
        [sys.executable, str(BACKEND_DIR / "batch_import.py"), str(matchday)],
        cwd=BACKEND_DIR,
        check=True,
    )

    if args.no_push:
        print("Import gespeichert; Veröffentlichung wurde übersprungen.")
        return

    print(publish_generated_data(matchday))


if __name__ == "__main__":
    main()
