from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import Locator, sync_playwright


BACKEND_DIR = Path(__file__).resolve().parent
AUTH_FILE = BACKEND_DIR / "secrets" / "kicktipp-auth.json"
OUTPUT_DIR = BACKEND_DIR / "data"

TIPPSAISON_ID = "3923606"

KICKTIPP_NAMES = {
    "Daniel": "Daniel",
    "Tim": "Tim",
    "Marcus": "Marcus",
    "Simon": "Simon",
    "Björn": "Björn",
    "Alex": "Alex",
    "KAIANO": "Kai",
    "AllezEffzeh": "Jan",
    "Luitpold": "Marius",
}

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
    kicktipp_name: str
    raw_points: int


class ScoredResult(TypedDict):
    rank: int
    name: str
    kicktipp_name: str
    raw_points: int
    ts_points: int


def build_url(matchday: int) -> str:
    return (
        "https://www.kicktipp.de/tasmania-hackentrick/"
        "tippuebersicht"
        f"?tippsaisonId={TIPPSAISON_ID}"
        f"&spieltagIndex={matchday}"
    )


def parse_score(score_text: str) -> int:
    cleaned = re.sub(r"[^\d-]", "", score_text)

    if not cleaned:
        raise ValueError(
            f"Die Punktzahl konnte nicht gelesen werden: {score_text!r}"
        )

    return int(cleaned)


def read_results(page) -> list[RawResult]:
    name_elements = page.locator(".mg_name")
    results: list[RawResult] = []

    for index in range(name_elements.count()):
        name_element = name_elements.nth(index)
        kicktipp_name = name_element.inner_text().strip()

        if kicktipp_name not in KICKTIPP_NAMES:
            continue

        row: Locator = name_element.locator("xpath=ancestor::tr[1]")
        cells = row.locator("td")

        if cells.count() < 3:
            raise ValueError(
                f"Zu wenige Tabellenzellen bei {kicktipp_name}."
            )

        # Bei Kicktipp ist die Spieltagssumme die drittletzte Zelle.
        score_text = cells.nth(cells.count() - 3).inner_text().strip()
        raw_points = parse_score(score_text)

        results.append(
            {
                "name": KICKTIPP_NAMES[kicktipp_name],
                "kicktipp_name": kicktipp_name,
                "raw_points": raw_points,
            }
        )

    return results


def validate_results(results: list[RawResult]) -> None:
    expected_names = set(KICKTIPP_NAMES.values())
    actual_names = {result["name"] for result in results}

    missing_names = expected_names - actual_names

    if len(results) != 9:
        raise ValueError(
            f"Es wurden {len(results)} statt 9 Ergebnisse erkannt."
        )

    if missing_names:
        raise ValueError(
            "Folgende Teilnehmer fehlen: "
            + ", ".join(sorted(missing_names))
        )


def assign_ranking_points(
    raw_results: list[RawResult],
) -> list[ScoredResult]:
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

        scored_results.append(
            {
                "rank": current_rank,
                "name": result["name"],
                "kicktipp_name": result["kicktipp_name"],
                "raw_points": result["raw_points"],
                "ts_points": RANKING_POINTS.get(current_rank, 0),
            }
        )

        previous_raw_points = result["raw_points"]

    return scored_results


def save_result(
    matchday: int,
    source_url: str,
    results: list[ScoredResult],
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"kicktipp_matchday_{matchday:02d}.json"

    payload = {
        "source": "kicktipp",
        "competition": "tippspiel",
        "tippsaison_id": TIPPSAISON_ID,
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

        print(f"Öffne Kicktipp-Spieltag {matchday} …")

        page.goto(
            source_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_selector(
            ".mg_name",
            timeout=60_000,
        )

        raw_results = read_results(page)
        validate_results(raw_results)

        scored_results = assign_ranking_points(raw_results)

        print()
        print(f"Tippspielwertung – Spieltag {matchday}")
        print("-" * 55)
        print(
            f"{'Rang':<6}"
            f"{'Spieler':<12}"
            f"{'Rohpunkte':>12}"
            f"{'TS-Punkte':>12}"
        )
        print("-" * 55)

        for result in scored_results:
            print(
                f"{result['rank']:<6}"
                f"{result['name']:<12}"
                f"{result['raw_points']:>12}"
                f"{result['ts_points']:>12}"
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