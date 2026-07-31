from __future__ import annotations

import argparse
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, sync_playwright

import process_kicker_matchday as kicker
import process_kicktipp_matchday as kicktipp
from combine_matchday import (
    combine_matchday,
    save_combined_matchday,
    update_public_data,
)


BACKEND_DIR = Path(__file__).resolve().parent
LOG_FILE = BACKEND_DIR / "data" / "batch_import_log.json"


def import_kicker_matchday(
    page: Page,
    matchday: int,
) -> Path:
    """Ruft einen kicker-Spieltag ab und speichert dessen MS-Wertung."""
    source_url = kicker.build_url(matchday)

    print(f"  kicker: Öffne Spieltag {matchday} …")

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

    complete_blocks: list[list[kicker.RawResult]] = []

    for table_index in range(ranking_tables.count()):
        results = kicker.read_ranking_block(
            ranking_tables.nth(table_index)
        )

        if len(results) == 9:
            complete_blocks.append(results)

    if not complete_blocks:
        raise RuntimeError(
            "Keine vollständige kicker-Spieltagsrangliste gefunden."
        )

    # Auf der /group/round/-Seite ist der erste vollständige
    # Ranglistenblock die Spieltagswertung.
    raw_results = complete_blocks[0]

    kicker.validate_results(raw_results)

    scored_results = kicker.assign_ranking_points(
        raw_results
    )

    return kicker.save_result(
        matchday=matchday,
        source_url=source_url,
        results=scored_results,
    )


def import_kicktipp_matchday(
    page: Page,
    matchday: int,
) -> Path:
    """Ruft einen Kicktipp-Spieltag ab und speichert dessen TS-Wertung."""
    source_url = kicktipp.build_url(matchday)

    print(f"  Kicktipp: Öffne Spieltag {matchday} …")

    page.goto(
        source_url,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    page.wait_for_selector(
        ".mg_name",
        timeout=60_000,
    )

    raw_results = kicktipp.read_results(page)
    kicktipp.validate_results(raw_results)

    scored_results = kicktipp.assign_ranking_points(
        raw_results
    )

    return kicktipp.save_result(
        matchday=matchday,
        source_url=source_url,
        results=scored_results,
    )


def save_log(log_entries: list[dict[str, Any]]) -> None:
    """Speichert das Protokoll des Mehrfachimports."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "entries": log_entries,
    }

    LOG_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def create_context(
    browser,
    auth_file: Path,
) -> BrowserContext:
    if not auth_file.exists():
        raise FileNotFoundError(
            f"Anmeldedatei fehlt: {auth_file}"
        )

    return browser.new_context(
        storage_state=str(auth_file)
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Importiert mehrere Spieltage von kicker und Kicktipp."
        )
    )

    parser.add_argument(
        "--start",
        type=int,
        default=32,
        help="Erster zu importierender Spieltag.",
    )

    parser.add_argument(
        "--end",
        type=int,
        default=34,
        help="Letzter zu importierender Spieltag.",
    )

    parser.add_argument(
        "--pause",
        type=float,
        default=2.0,
        help="Pause zwischen zwei Spieltagen in Sekunden.",
    )

    args = parser.parse_args()

    if not 1 <= args.start <= 34:
        parser.error("--start muss zwischen 1 und 34 liegen.")

    if not 1 <= args.end <= 34:
        parser.error("--end muss zwischen 1 und 34 liegen.")

    if args.start > args.end:
        parser.error("--start darf nicht größer als --end sein.")

    log_entries: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge",
            headless=False,
        )

        kicker_context = create_context(
            browser,
            kicker.AUTH_FILE,
        )

        kicktipp_context = create_context(
            browser,
            kicktipp.AUTH_FILE,
        )

        kicker_page = kicker_context.new_page()
        kicktipp_page = kicktipp_context.new_page()

        for matchday in range(args.start, args.end + 1):
            print()
            print("=" * 60)
            print(f"Importiere Spieltag {matchday}")
            print("=" * 60)

            started_at = datetime.now().astimezone()

            try:
                kicker_file = import_kicker_matchday(
                    kicker_page,
                    matchday,
                )

                kicktipp_file = import_kicktipp_matchday(
                    kicktipp_page,
                    matchday,
                )

                combined_payload = combine_matchday(matchday)

                combined_file = save_combined_matchday(
                    matchday,
                    combined_payload,
                )

                public_file = update_public_data(
                    combined_payload
                )

                print(f"  Erfolgreich: Spieltag {matchday}")
                print(f"  kicker:    {kicker_file.name}")
                print(f"  Kicktipp:  {kicktipp_file.name}")
                print(f"  Kombiniert:{combined_file.name}")
                print(f"  PWA-Daten: {public_file}")

                log_entries.append(
                    {
                        "matchday": matchday,
                        "status": "success",
                        "started_at": started_at.isoformat(),
                        "finished_at": (
                            datetime.now()
                            .astimezone()
                            .isoformat()
                        ),
                    }
                )

            except Exception as error:
                print()
                print(
                    f"  FEHLER bei Spieltag {matchday}: "
                    f"{error}"
                )

                traceback.print_exc()

                log_entries.append(
                    {
                        "matchday": matchday,
                        "status": "error",
                        "started_at": started_at.isoformat(),
                        "finished_at": (
                            datetime.now()
                            .astimezone()
                            .isoformat()
                        ),
                        "error": str(error),
                    }
                )

            save_log(log_entries)

            if matchday < args.end:
                print(
                    f"  Warte {args.pause:.1f} Sekunden …"
                )
                time.sleep(args.pause)

        kicker_context.close()
        kicktipp_context.close()
        browser.close()

    successes = sum(
        entry["status"] == "success"
        for entry in log_entries
    )

    errors = sum(
        entry["status"] == "error"
        for entry in log_entries
    )

    print()
    print("=" * 60)
    print("Mehrfachimport beendet")
    print("=" * 60)
    print(f"Erfolgreich: {successes}")
    print(f"Fehler:      {errors}")
    print(f"Protokoll:   {LOG_FILE}")


if __name__ == "__main__":
    main()