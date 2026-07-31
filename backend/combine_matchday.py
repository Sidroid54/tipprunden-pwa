from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

INPUT_DIR = BACKEND_DIR / "data"
DOCS_DIR = PROJECT_DIR / "docs"

PARTICIPANTS = [
    "Björn",
    "Jan",
    "Marcus",
    "Marius",
    "Kai",
    "Alex",
    "Tim",
    "Daniel",
    "Simon",
]


def load_json(path: Path) -> dict[str, Any]:
    """Lädt eine JSON-Datei und prüft, ob sie existiert."""
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def results_by_name(
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Ordnet die Ergebnisse eines Imports nach Teilnehmernamen."""
    results = payload.get("results")

    if not isinstance(results, list):
        raise ValueError(
            f"Ungültiges Ergebnisformat bei Quelle "
            f"{payload.get('source', 'unbekannt')}."
        )

    indexed: dict[str, dict[str, Any]] = {}

    for result in results:
        name = result.get("name")

        if name in indexed:
            raise ValueError(f"Teilnehmer doppelt vorhanden: {name}")

        indexed[name] = result

    return indexed


def validate_names(
    source_name: str,
    indexed_results: dict[str, dict[str, Any]],
) -> None:
    """Prüft, ob genau alle neun Teilnehmer enthalten sind."""
    expected = set(PARTICIPANTS)
    actual = set(indexed_results)

    missing = expected - actual
    unexpected = actual - expected

    if missing:
        raise ValueError(
            f"{source_name}: Teilnehmer fehlen: "
            + ", ".join(sorted(missing))
        )

    if unexpected:
        raise ValueError(
            f"{source_name}: Unbekannte Teilnehmer: "
            + ", ".join(sorted(unexpected))
        )


def competition_ranking(
    rows: list[dict[str, Any]],
    points_field: str,
) -> list[dict[str, Any]]:
    """
    Sortiert nach Punkten und vergibt Competition-Ränge.

    Beispiel:
    15, 15, 12 -> Rang 1, 1, 3
    """
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -int(row[points_field]),
            row["name"].casefold(),
        ),
    )

    previous_points: int | None = None
    current_rank = 0

    for index, row in enumerate(sorted_rows):
        points = int(row[points_field])
        position = index + 1

        if points != previous_points:
            current_rank = position

        row["matchday_rank"] = current_rank
        previous_points = points

    return sorted_rows


def combine_matchday(matchday: int) -> dict[str, Any]:
    """Führt Kicktipp- und kicker-Ergebnisse zusammen."""
    kicktipp_file = (
        INPUT_DIR / f"kicktipp_matchday_{matchday:02d}.json"
    )
    kicker_file = (
        INPUT_DIR / f"kicker_matchday_{matchday:02d}.json"
    )

    kicktipp_payload = load_json(kicktipp_file)
    kicker_payload = load_json(kicker_file)

    kicktipp_matchday = kicktipp_payload.get("matchday")
    kicker_matchday = kicker_payload.get("matchday")

    if kicktipp_matchday != matchday:
        raise ValueError(
            f"Kicktipp-Datei gehört zu Spieltag "
            f"{kicktipp_matchday}, erwartet wurde {matchday}."
        )

    if kicker_matchday != matchday:
        raise ValueError(
            f"kicker-Datei gehört zu Spieltag "
            f"{kicker_matchday}, erwartet wurde {matchday}."
        )

    kicktipp_results = results_by_name(kicktipp_payload)
    kicker_results = results_by_name(kicker_payload)

    validate_names("Kicktipp", kicktipp_results)
    validate_names("kicker", kicker_results)

    combined_rows: list[dict[str, Any]] = []

    for name in PARTICIPANTS:
        ts = kicktipp_results[name]
        ms = kicker_results[name]

        ts_points = int(ts["ts_points"])
        ms_points = int(ms["ms_points"])

        combined_rows.append(
            {
                "name": name,
                "ts": {
                    "rank": int(ts["rank"]),
                    "raw_points": int(ts["raw_points"]),
                    "points": ts_points,
                },
                "ms": {
                    "rank": int(ms["rank"]),
                    "raw_points": int(ms["raw_points"]),
                    "points": ms_points,
                },
                "matchday_points": ts_points + ms_points,
            }
        )

    ranked_rows = competition_ranking(
        combined_rows,
        points_field="matchday_points",
    )

    return {
        "matchday": matchday,
        "generated_at": datetime.now().astimezone().isoformat(),
        "results": ranked_rows,
        "sources": {
            "kicktipp": {
                "retrieved_at": kicktipp_payload.get(
                    "retrieved_at"
                ),
                "source_url": kicktipp_payload.get("source_url"),
            },
            "kicker": {
                "retrieved_at": kicker_payload.get(
                    "retrieved_at"
                ),
                "source_url": kicker_payload.get("source_url"),
            },
        },
    }


def save_combined_matchday(
    matchday: int,
    payload: dict[str, Any],
) -> Path:
    """Speichert die kombinierte Spieltagsdatei im Backend."""
    output_file = (
        INPUT_DIR / f"combined_matchday_{matchday:02d}.json"
    )

    output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_file


def update_public_data(
    matchday_payload: dict[str, Any],
) -> Path:
    """
    Aktualisiert docs/data.json.

    Bereits vorhandene Spieltage bleiben erhalten und der aktuelle
    Spieltag wird ergänzt oder ersetzt.
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    public_file = DOCS_DIR / "data.json"

    if public_file.exists():
        public_payload = load_json(public_file)
    else:
        public_payload = {
            "app": "Tasmania Hackentrick",
            "participants": PARTICIPANTS,
            "matchdays": [],
        }

    existing_matchdays = public_payload.get("matchdays", [])

    if not isinstance(existing_matchdays, list):
        raise ValueError(
            "docs/data.json enthält keine gültige "
            "Spieltagsliste."
        )

    matchday_number = matchday_payload["matchday"]

    remaining_matchdays = [
        item
        for item in existing_matchdays
        if item.get("matchday") != matchday_number
    ]

    remaining_matchdays.append(matchday_payload)
    remaining_matchdays.sort(
        key=lambda item: int(item["matchday"])
    )

    public_payload["app"] = "Tasmania Hackentrick"
    public_payload["participants"] = PARTICIPANTS
    public_payload["updated_at"] = (
        datetime.now().astimezone().isoformat()
    )
    public_payload["matchdays"] = remaining_matchdays

    public_file.write_text(
        json.dumps(
            public_payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return public_file


def print_table(payload: dict[str, Any]) -> None:
    """Zeigt die gemeinsame Spieltagswertung in PowerShell."""
    print()
    print(
        f"Gesamtwertung – Spieltag {payload['matchday']}"
    )
    print("-" * 77)
    print(
        f"{'Rang':<6}"
        f"{'Spieler':<12}"
        f"{'TS':>7}"
        f"{'MS':>7}"
        f"{'Gesamt':>10}"
        f"{'TS roh':>11}"
        f"{'MS roh':>11}"
    )
    print("-" * 77)

    for result in payload["results"]:
        print(
            f"{result['matchday_rank']:<6}"
            f"{result['name']:<12}"
            f"{result['ts']['points']:>7}"
            f"{result['ms']['points']:>7}"
            f"{result['matchday_points']:>10}"
            f"{result['ts']['raw_points']:>11}"
            f"{result['ms']['raw_points']:>11}"
        )


def main() -> None:
    matchday = 33

    payload = combine_matchday(matchday)
    print_table(payload)

    backend_file = save_combined_matchday(
        matchday,
        payload,
    )
    public_file = update_public_data(payload)

    print()
    print("Kombinierte Datei gespeichert:")
    print(backend_file)

    print()
    print("Öffentliche PWA-Daten aktualisiert:")
    print(public_file)


if __name__ == "__main__":
    main()