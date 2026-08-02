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

KICKER_SEASON_ID = "se-k00012025"
KICKER_ROUND_PREFIX = "rn-k00012025"
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

KICKTIPP_SEASON_ID = "3923606"

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
