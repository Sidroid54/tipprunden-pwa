import argparse
from pathlib import Path
import re

from playwright.sync_api import sync_playwright

from config import (
    KICKER_GROUP_ID as GROUP_ID,
    KICKER_NAMES,
    KICKER_ROUND_PREFIX as ROUND_PREFIX,
    KICKER_SEASON_ID as SEASON_ID,
    validate_matchday,
)


BACKEND_DIR = Path(__file__).resolve().parent
AUTH_FILE = BACKEND_DIR / "secrets" / "kicker-auth.json"

def build_url(matchday: int) -> str:
    round_id = f"{ROUND_PREFIX}{matchday:04d}"

    return (
        "https://www.kicker.de/managerspiel/interactive/"
        f"{SEASON_ID}/group/round/{round_id}/{GROUP_ID}"
    )


def clean_name(name: str) -> str:
    return re.sub(r"\s*\(Admin\)\s*", "", name).strip()


def parse_score(score_text: str) -> int:
    cleaned = re.sub(r"[^\d-]", "", score_text)

    if not cleaned:
        raise ValueError(f"Ungültige Punktzahl: {score_text!r}")

    return int(cleaned)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Liest einen kicker-Spieltag zur Kontrolle aus."
    )
    parser.add_argument("matchday", type=int, help="Spieltag von 1 bis 34.")
    args = parser.parse_args()

    try:
        matchday = validate_matchday(args.matchday)
    except ValueError as error:
        parser.error(str(error))

    url = build_url(matchday)

    if not AUTH_FILE.exists():
        raise FileNotFoundError(
            f"Anmeldedatei nicht gefunden: {AUTH_FILE}"
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
            url,
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

        print(
            f"Gefundene Ranglistenblöcke: "
            f"{ranking_tables.count()}"
        )

        possible_results: list[list[dict[str, object]]] = []

        for table_index in range(ranking_tables.count()):
            table = ranking_tables.nth(table_index)
            rows = table.locator("tr.ranking-item")

            results: list[dict[str, object]] = []

            for row_index in range(rows.count()):
                row = rows.nth(row_index)

                name_locator = row.locator(
                    ".ranking-item__name"
                )
                score_locator = row.locator(
                    ".ranking-item__score"
                )

                if (
                    name_locator.count() == 0
                    or score_locator.count() == 0
                ):
                    continue

                source_name = clean_name(
                    name_locator.inner_text()
                )

                if source_name not in KICKER_NAMES:
                    continue

                score = parse_score(
                    score_locator.inner_text()
                )

                results.append(
                    {
                        "name": KICKER_NAMES[source_name],
                        "kicker_name": source_name,
                        "raw_points": score,
                    }
                )

            if len(results) == 9:
                possible_results.append(results)

        print()
        print(
            "Vollständige Ranglisten mit neun "
            f"Teilnehmern: {len(possible_results)}"
        )

        for index, results in enumerate(possible_results):
            print()
            print(f"Ranglistenblock {index + 1}")

            for result in results:
                print(
                    f"{result['name']:7} "
                    f"{result['raw_points']:4} Punkte"
                )

        input(
            "\nKontrolliere die Ausgabe und drücke Enter …"
        )

        browser.close()


if __name__ == "__main__":
    main()
