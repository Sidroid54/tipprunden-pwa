from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import Locator, sync_playwright


BACKEND_DIR = Path(__file__).resolve().parent
AUTH_FILE = BACKEND_DIR / "secrets" / "kicker-auth.json"
OUTPUT_DIR = BACKEND_DIR / "data"

SEASON_ID = "se-k00012025"
ROUND_PREFIX = "rn-k00012025"
GROUP_ID = "010000000000000000000711"

# Deine Zuordnung der kicker-Namen zu den Namen in unserer App.
KICKER_NAMES = {
    "Simon Owald": "Simon",
    "Jan Horstmann": "Jan",
    "Daniel Sinzig": "Daniel",
    "Luitpold": "Marius",
    "KAIANO": "Kai",
    "Tim Roth": "Tim",
    "Marcus Vanselow": "Marcus",
    "björn wagner": "Björn",
    "Alexander Neubauer": "Alex",
}

# Punkte nach Rang.
RANKING_POINTS = {
    1: 10,
    2: 8,
    3: 7,
    4: 6,
    5: 5,
    6: 4,
    7: 3,
    8: 2,
    9: 1,
}


class RawResult(TypedDict):
    name: str
    kicker_name: str
    raw_points: int


class ScoredResult(TypedDict):
    rank: int
    name: str
    kicker_name: str
    raw_points: int
    ms_points: int


def build_url(matchday: int) -> str:
    """Erzeugt die kicker-URL für einen bestimmten Spieltag."""
    round_id = f"{ROUND_PREFIX}{matchday:04d}"

    return (
        "https://www.kicker.de/managerspiel/interactive/"
        f"{SEASON_ID}/group/round/{round_id}/{GROUP_ID}"
    )


def clean_name(name: str) -> str:
    """Entfernt Zusätze wie '(Admin)' und überflüssige Leerzeichen."""
    cleaned = re.sub(r"\s*\(Admin\)\s*", "", name, flags=re.IGNORECASE)
    return cleaned.strip()


def parse_score(score_text: str) -> int:
    """Wandelt einen angezeigten Punktetext in eine ganze Zahl um."""
    cleaned = re.sub(r"[^\d-]", "", score_text)

    if not cleaned:
        raise ValueError(
            f"Die Punktzahl konnte nicht gelesen werden: {score_text!r}"
        )

    return int(cleaned)


def read_ranking_block(table: Locator) -> list[RawResult]:
    """Liest einen einzelnen kicker-Ranglistenblock aus."""
    rows = table.locator("tr.ranking-item")
    results: list[RawResult] = []

    for row_index in range(rows.count()):
        row = rows.nth(row_index)

        name_locator = row.locator(".ranking-item__name")
        score_locator = row.locator(".ranking-item__score")

        if name_locator.count() == 0 or score_locator.count() == 0:
            continue

        kicker_name = clean_name(name_locator.inner_text())

        if kicker_name not in KICKER_NAMES:
            continue

        raw_points = parse_score(score_locator.inner_text())

        results.append(
            {
                "name": KICKER_NAMES[kicker_name],
                "kicker_name": kicker_name,
                "raw_points": raw_points,
            }
        )

    return results


def assign_ranking_points(
    raw_results: list[RawResult],
) -> list[ScoredResult]:
    """
    Vergibt die Tasmania-Wertungspunkte.

    Bei Gleichstand erhalten alle den gleichen Rang und die gleiche
    Rangpunktzahl. Der nächste Rang wird entsprechend übersprungen.

    Beispiel:
    1., 1., 3. -> 10, 10, 7 Punkte
    """
    sorted_results = sorted(
        raw_results,
        key=lambda result: result["raw_points"],
        reverse=True,
    )

    scored_results: list[ScoredResult] = []

    previous_raw_points: int | None = None
    current_rank = 0

    for index, result in enumerate(sorted_results):
        position = index + 1

        if result["raw_points"] != previous_raw_points:
            current_rank = position

        ms_points = RANKING_POINTS.get(current_rank, 0)

        scored_results.append(
            {
                "rank": current_rank,
                "name": result["name"],
                "kicker_name": result["kicker_name"],
                "raw_points": result["raw_points"],
                "ms_points": ms_points,
            }
        )

        previous_raw_points = result["raw_points"]

    return scored_results


def validate_results(results: list[RawResult]) -> None:
    """Prüft, ob genau alle neun Teilnehmer erkannt wurden."""
    expected_names = set(KICKER_NAMES.values())
    actual_names = {result["name"] for result in results}

    missing_names = expected_names - actual_names
    unexpected_names = actual_names - expected_names

    if len(results) != 9:
        raise ValueError(
            f"Es wurden {len(results)} statt 9 Ergebnisse erkannt."
        )

    if missing_names:
        raise ValueError(
            "Folgende Teilnehmer fehlen: "
            + ", ".join(sorted(missing_names))
        )

    if unexpected_names:
        raise ValueError(
            "Unerwartete Teilnehmer: "
            + ", ".join(sorted(unexpected_names))
        )


def save_result(
    matchday: int,
    source_url: str,
    results: list[ScoredResult],
) -> Path:
    """Speichert das Ergebnis als JSON-Datei."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"kicker_matchday_{matchday:02d}.json"

    payload = {
        "source": "kicker",
        "competition": "managerspiel_interactive",
        "season_id": SEASON_ID,
        "matchday": matchday,
        "source_url": source_url,
        "retrieved_at": datetime.now().astimezone().isoformat(),
        "results": results,
    }

    output_file.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_file


def main() -> None:
    matchday = 33
    source_url = build_url(matchday)

    if not AUTH_FILE.exists():
        raise FileNotFoundError(
            f"Die Anmeldedatei wurde nicht gefunden: {AUTH_FILE}"
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge",
            headless=False,
        )

        context = browser.new_context(
            storage_state=str(AUTH_FILE)
        )

        page = context.new_page()

        print(f"Öffne kicker-Spieltag {matchday} …")

        page.goto(
            source_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_selector(
            "tr.ranking-item",
            timeout=60_000,
        )

        ranking_tables = page.locator(
            "tbody:has(tr.ranking-item)"
        )

        complete_blocks: list[list[RawResult]] = []

        for table_index in range(ranking_tables.count()):
            results = read_ranking_block(
                ranking_tables.nth(table_index)
            )

            if len(results) == 9:
                complete_blocks.append(results)

        print(
            f"Vollständige Ranglistenblöcke: "
            f"{len(complete_blocks)}"
        )

        if not complete_blocks:
            raise RuntimeError(
                "Es wurde keine vollständige Rangliste gefunden."
            )

        # Auf der bestätigten /group/round/-Seite ist der erste
        # vollständige Block die Spieltagswertung.
        matchday_results = complete_blocks[0]

        validate_results(matchday_results)

        scored_results = assign_ranking_points(
            matchday_results
        )

        print()
        print(f"Managerspielwertung – Spieltag {matchday}")
        print("-" * 55)
        print(
            f"{'Rang':<6}"
            f"{'Spieler':<12}"
            f"{'Rohpunkte':>12}"
            f"{'MS-Punkte':>12}"
        )
        print("-" * 55)

        for result in scored_results:
            print(
                f"{result['rank']:<6}"
                f"{result['name']:<12}"
                f"{result['raw_points']:>12}"
                f"{result['ms_points']:>12}"
            )

        output_file = save_result(
            matchday=matchday,
            source_url=source_url,
            results=scored_results,
        )

        print()
        print("Ergebnis gespeichert unter:")
        print(output_file)

        input("\nDrücke Enter, um den Browser zu schließen …")

        browser.close()


if __name__ == "__main__":
    main()