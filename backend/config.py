"""Zentrale Konfiguration der Tasmania-Hackentrick-Wertung."""

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

CURRENT_SEASON = "2026-27"
ARCHIVED_SEASONS = ("2025-26",)

SEASONS = {
    "2026-27": {
        "label": "Saison 2026/27",
        "kicker_season_id": "se-k00012026",
        "kicker_round_prefix": "rn-k00012026",
        "kicktipp_season_id": "5500429",
    },
    "2025-26": {
        "label": "Saison 2025/26",
        "kicker_season_id": "se-k00012025",
        "kicker_round_prefix": "rn-k00012025",
        "kicktipp_season_id": "3923606",
    },
}

KICKER_SEASON_ID = SEASONS[CURRENT_SEASON]["kicker_season_id"]
KICKER_ROUND_PREFIX = SEASONS[CURRENT_SEASON]["kicker_round_prefix"]
KICKER_GROUP_ID = "010000000000000000000711"

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

KICKTIPP_SEASON_ID = SEASONS[CURRENT_SEASON]["kicktipp_season_id"]

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


def validate_matchday(matchday: int) -> int:
    """Prüft und liefert einen gültigen Bundesliga-Spieltag."""
    if not 1 <= matchday <= 34:
        raise ValueError("Der Spieltag muss zwischen 1 und 34 liegen.")

    return matchday


def validate_season(season: str) -> str:
    """Prüft und liefert eine bekannte Saison-ID."""
    if season not in SEASONS:
        raise ValueError(f"Unbekannte Saison: {season}")

    return season


def validate_writable_season(season: str) -> str:
    """Verhindert Änderungen an archivierten Saisons."""
    validate_season(season)
    if season in ARCHIVED_SEASONS:
        raise ValueError(f"Die Saison {season} ist schreibgeschützt archiviert.")

    return season
