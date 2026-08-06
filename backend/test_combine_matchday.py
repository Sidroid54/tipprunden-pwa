import copy
import unittest

from combine_matchday import (
    combine_matchday,
    competition_ranking,
    save_combined_matchday,
    validate_combined_payload,
)
from config import PARTICIPANTS


class CombineMatchdayTests(unittest.TestCase):
    def test_competition_ranking_handles_ties(self) -> None:
        rows = [
            {"name": "Marcus", "points": 12},
            {"name": "Jan", "points": 15},
            {"name": "Björn", "points": 15},
        ]

        ranking = competition_ranking(rows, "points")

        self.assertEqual(
            [(row["name"], row["matchday_rank"]) for row in ranking],
            [("Björn", 1), ("Jan", 1), ("Marcus", 3)],
        )

    def test_existing_matchday_is_combined_completely(self) -> None:
        payload = combine_matchday(34, "2025-26")

        self.assertEqual(payload["matchday"], 34)
        self.assertEqual(len(payload["results"]), len(PARTICIPANTS))
        self.assertEqual(
            {row["name"] for row in payload["results"]},
            set(PARTICIPANTS),
        )

        for row in payload["results"]:
            with self.subTest(name=row["name"]):
                self.assertEqual(
                    row["matchday_points"],
                    row["ts"]["points"] + row["ms"]["points"],
                )

    def test_invalid_total_is_rejected_before_publication(self) -> None:
        payload = copy.deepcopy(combine_matchday(34, "2025-26"))
        payload["results"][0]["matchday_points"] += 1

        with self.assertRaisesRegex(ValueError, "Falsche Spieltagssumme"):
            validate_combined_payload(payload)

    def test_archived_season_cannot_be_overwritten(self) -> None:
        payload = combine_matchday(34, "2025-26")

        with self.assertRaisesRegex(ValueError, "schreibgeschützt"):
            save_combined_matchday(34, payload, "2025-26")


if __name__ == "__main__":
    unittest.main()
