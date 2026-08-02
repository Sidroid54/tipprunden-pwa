import unittest

from config import validate_matchday
from process_kicker_matchday import assign_ranking_points as score_kicker
from process_kicktipp_matchday import assign_ranking_points as score_kicktipp


class RankingPointsTests(unittest.TestCase):
    def test_kicker_tie_uses_competition_ranks(self) -> None:
        results = score_kicker(
            [
                {
                    "name": "Björn",
                    "kicker_name": "Björn",
                    "raw_points": 80,
                },
                {
                    "name": "Jan",
                    "kicker_name": "Jan",
                    "raw_points": 80,
                },
                {
                    "name": "Marcus",
                    "kicker_name": "Marcus",
                    "raw_points": 70,
                },
            ]
        )

        self.assertEqual([row["rank"] for row in results], [1, 1, 3])
        self.assertEqual([row["ms_points"] for row in results], [10, 10, 7])

    def test_kicktipp_sorts_and_scores_all_places(self) -> None:
        raw_points = [3, 9, 6, 1, 8, 4, 7, 2, 5]
        results = score_kicktipp(
            [
                {
                    "name": f"Spieler {index}",
                    "kicktipp_name": f"Spieler {index}",
                    "raw_points": points,
                }
                for index, points in enumerate(raw_points, start=1)
            ]
        )

        self.assertEqual(
            [row["raw_points"] for row in results],
            list(range(9, 0, -1)),
        )
        self.assertEqual(
            [row["ts_points"] for row in results],
            [10, 8, 7, 6, 5, 4, 3, 2, 1],
        )

    def test_matchday_validation_accepts_boundaries(self) -> None:
        self.assertEqual(validate_matchday(1), 1)
        self.assertEqual(validate_matchday(34), 34)

    def test_matchday_validation_rejects_out_of_range_values(self) -> None:
        for matchday in (0, 35):
            with self.subTest(matchday=matchday):
                with self.assertRaisesRegex(ValueError, "zwischen 1 und 34"):
                    validate_matchday(matchday)


if __name__ == "__main__":
    unittest.main()
