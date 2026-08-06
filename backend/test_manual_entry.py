import unittest

from config import PARTICIPANTS
from manual_entry import build_manual_matchday


class ManualEntryTests(unittest.TestCase):
    def test_manual_entry_builds_complete_valid_ranking(self) -> None:
        scores = {
            name: {
                "ts_raw_points": index,
                "ms_raw_points": index * 10,
            }
            for index, name in enumerate(PARTICIPANTS, start=1)
        }

        _, _, combined = build_manual_matchday(1, scores)

        self.assertEqual(combined["season"], "2026-27")
        self.assertEqual(len(combined["results"]), len(PARTICIPANTS))
        self.assertEqual(combined["results"][0]["matchday_points"], 20)

    def test_manual_entry_rejects_missing_participant(self) -> None:
        scores = {
            name: {"ts_raw_points": 1, "ms_raw_points": 1}
            for name in PARTICIPANTS[:-1]
        }

        with self.assertRaisesRegex(ValueError, "genau alle Teilnehmer"):
            build_manual_matchday(1, scores)


if __name__ == "__main__":
    unittest.main()
