from __future__ import annotations

import argparse
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
from config import validate_matchday
from file_utils import write_json_atomic


BACKEND_DIR = Path(__file__).resolve().parent
LOG_FILE = BACKEND_DIR / "data" / "batch_import_log.json"
DIAGNOSTICS_DIR = BACKEND_DIR / "diagnostics"


def import_kicker_matchday(
    page: Page,
    matchday: int,
) -> tuple[str, list[kicker.ScoredResult]]:
    """Ruft einen kicker-Spieltag ab, ohne bestehende Dateien zu ändern."""
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

    return source_url, scored_results


def import_kicktipp_matchday(
    page: Page,
    matchday: int,
) -> tuple[str, list[kicktipp.ScoredResult]]:
    """Ruft einen Kicktipp-Spieltag ab, ohne bestehende Dateien zu ändern."""
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

    return source_url, scored_results


def save_log(log_entries: list[dict[str, Any]]) -> None:
    """Speichert das Protokoll des Mehrfachimports."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "entries": log_entries,
    }

    write_json_atomic(LOG_FILE, payload)


def save_diagnostics(
    matchday: int,
    pages: dict[str, Page],
) -> list[Path]:
    """Speichert bei Importfehlern Screenshots der beteiligten Seiten."""
    DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    saved_files: list[Path] = []

    for source, page in pages.items():
        output_file = (
            DIAGNOSTICS_DIR
            / f"matchday-{matchday:02d}-{source}-{timestamp}.png"
        )

        try:
            page.screenshot(path=str(output_file), full_page=True)
            saved_files.append(output_file)
        except Exception as screenshot_error:
            print(
                f"  Diagnose-Screenshot für {source} fehlgeschlagen: "
                f"{screenshot_error}"
            )

    return saved_files


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
        "matchday",
        nargs="?",
        type=int,
        help=(
            "Ein einzelner Spieltag von 1 bis 34. "
            "Alternativ --start und --end verwenden."
        ),
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

    if args.matchday is not None:
        if args.start != 32 or args.end != 34:
            parser.error(
                "Spieltag nicht zusammen mit --start oder --end verwenden."
            )

        args.start = args.matchday
        args.end = args.matchday

    try:
        validate_matchday(args.start)
        validate_matchday(args.end)
    except ValueError as error:
        parser.error(str(error))

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
                kicker_url, kicker_results = import_kicker_matchday(
                    kicker_page,
                    matchday,
                )

                kicktipp_url, kicktipp_results = import_kicktipp_matchday(
                    kicktipp_page,
                    matchday,
                )

                # Beide Abrufe müssen erfolgreich sein, bevor Quelldateien
                # ersetzt werden.
                kicker_file = kicker.save_result(
                    matchday, kicker_url, kicker_results
                )
                kicktipp_file = kicktipp.save_result(
                    matchday, kicktipp_url, kicktipp_results
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

                diagnostic_files = save_diagnostics(
                    matchday,
                    {"kicker": kicker_page, "kicktipp": kicktipp_page},
                )

                if diagnostic_files:
                    print("  Diagnose gespeichert:")
                    for diagnostic_file in diagnostic_files:
                        print(f"    {diagnostic_file}")

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
                        "diagnostics": [
                            str(path) for path in diagnostic_files
                        ],
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
