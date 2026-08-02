"""Sichere Dateioperationen für Importdaten."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_json_atomic(path: Path, payload: Any) -> None:
    """Schreibt JSON vollständig, bevor eine bestehende Datei ersetzt wird."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")

    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
