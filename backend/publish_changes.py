"""Veröffentlicht ausschließlich erzeugte Daten der aktuellen Saison."""

from __future__ import annotations

import subprocess
from pathlib import Path

from config import CURRENT_SEASON


PROJECT_DIR = Path(__file__).resolve().parent.parent


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        check=check,
        text=True,
        capture_output=True,
    )


def publish_generated_data(matchday: int) -> str:
    paths = [
        f"backend/data/{CURRENT_SEASON}",
        f"docs/data/{CURRENT_SEASON}.json",
        "docs/data.json",
    ]
    git("add", "--", *paths)

    staged = git("diff", "--cached", "--quiet", check=False)
    if staged.returncode == 0:
        return "Keine neuen Daten zu veröffentlichen."
    if staged.returncode != 1:
        raise RuntimeError(staged.stderr.strip() or "Git-Prüfung fehlgeschlagen.")

    message = f"Update matchday {matchday} for {CURRENT_SEASON}"
    git("commit", "-m", message)
    git("push", "origin", "main")
    return message
