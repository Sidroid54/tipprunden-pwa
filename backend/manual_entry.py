"""Manuelle Erfassung eines Spieltags als lokaler Scraping-Fallback."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from combine_matchday import (
    competition_ranking,
    save_combined_matchday,
    update_public_data,
    validate_combined_payload,
)
from config import CURRENT_SEASON, PARTICIPANTS, RANKING_POINTS, validate_matchday
from file_utils import write_json_atomic
from process_kicker_matchday import OUTPUT_DIR as KICKER_OUTPUT_DIR
from process_kicktipp_matchday import OUTPUT_DIR as KICKTIPP_OUTPUT_DIR


def score_competition(
    raw_scores: dict[str, int],
    points_key: str,
) -> list[dict[str, Any]]:
    rows = sorted(
        (
            {"name": name, "raw_points": int(raw_scores[name])}
            for name in PARTICIPANTS
        ),
        key=lambda row: (-row["raw_points"], row["name"].casefold()),
    )

    previous_score: int | None = None
    current_rank = 0

    for index, row in enumerate(rows):
        if row["raw_points"] != previous_score:
            current_rank = index + 1

        row["rank"] = current_rank
        row[points_key] = RANKING_POINTS.get(current_rank, 0)
        previous_score = row["raw_points"]

    return rows


def validate_manual_scores(scores: dict[str, Any]) -> None:
    if set(scores) != set(PARTICIPANTS):
        raise ValueError("Die Eingabe muss genau alle Teilnehmer enthalten.")

    for name, values in scores.items():
        if not isinstance(values, dict):
            raise ValueError(f"Ungültige Eingabe bei {name}.")

        for field in ("ts_raw_points", "ms_raw_points"):
            value = values.get(field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name}: {field} muss eine ganze Zahl sein.")

        if values["ts_raw_points"] < 0:
            raise ValueError(f"{name}: Tippspielpunkte dürfen nicht negativ sein.")


def build_manual_matchday(
    matchday: int,
    scores: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_matchday(matchday)
    validate_manual_scores(scores)

    ts_rows = score_competition(
        {name: scores[name]["ts_raw_points"] for name in PARTICIPANTS},
        "ts_points",
    )
    ms_rows = score_competition(
        {name: scores[name]["ms_raw_points"] for name in PARTICIPANTS},
        "ms_points",
    )
    ts_by_name = {row["name"]: row for row in ts_rows}
    ms_by_name = {row["name"]: row for row in ms_rows}

    combined_rows: list[dict[str, Any]] = []
    for name in PARTICIPANTS:
        ts = ts_by_name[name]
        ms = ms_by_name[name]
        combined_rows.append(
            {
                "name": name,
                "ts": {
                    "rank": ts["rank"],
                    "raw_points": ts["raw_points"],
                    "points": ts["ts_points"],
                },
                "ms": {
                    "rank": ms["rank"],
                    "raw_points": ms["raw_points"],
                    "points": ms["ms_points"],
                },
                "matchday_points": ts["ts_points"] + ms["ms_points"],
            }
        )

    ranked_rows = competition_ranking(combined_rows, "matchday_points")
    timestamp = datetime.now().astimezone().isoformat()
    manual_url = f"manual://{CURRENT_SEASON}/matchday/{matchday}"

    kicktipp_payload = {
        "source": "kicktipp",
        "competition": "tippspiel",
        "season": CURRENT_SEASON,
        "matchday": matchday,
        "source_url": manual_url,
        "retrieved_at": timestamp,
        "entry_method": "manual",
        "results": [
            {**row, "kicktipp_name": row["name"]} for row in ts_rows
        ],
    }
    kicker_payload = {
        "source": "kicker",
        "competition": "managerspiel_interactive",
        "season": CURRENT_SEASON,
        "matchday": matchday,
        "source_url": manual_url,
        "retrieved_at": timestamp,
        "entry_method": "manual",
        "results": [
            {**row, "kicker_name": row["name"]} for row in ms_rows
        ],
    }
    combined_payload = {
        "season": CURRENT_SEASON,
        "matchday": matchday,
        "generated_at": timestamp,
        "entry_method": "manual",
        "results": ranked_rows,
        "sources": {
            "kicktipp": {"retrieved_at": timestamp, "source_url": manual_url},
            "kicker": {"retrieved_at": timestamp, "source_url": manual_url},
        },
    }
    validate_combined_payload(combined_payload)
    return kicktipp_payload, kicker_payload, combined_payload


def save_manual_matchday(matchday: int, scores: dict[str, Any]) -> list[str]:
    kicktipp_payload, kicker_payload, combined_payload = build_manual_matchday(
        matchday, scores
    )
    kicktipp_file = KICKTIPP_OUTPUT_DIR / f"kicktipp_matchday_{matchday:02d}.json"
    kicker_file = KICKER_OUTPUT_DIR / f"kicker_matchday_{matchday:02d}.json"
    write_json_atomic(kicktipp_file, kicktipp_payload)
    write_json_atomic(kicker_file, kicker_payload)
    combined_file = save_combined_matchday(matchday, combined_payload)
    public_file = update_public_data(combined_payload)
    return [str(path) for path in (kicktipp_file, kicker_file, combined_file, public_file)]
