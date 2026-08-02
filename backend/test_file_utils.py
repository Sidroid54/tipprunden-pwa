import json
import tempfile
import unittest
from pathlib import Path

from file_utils import write_json_atomic


class AtomicJsonTests(unittest.TestCase):
    def test_json_is_written_and_temporary_file_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_file = Path(directory) / "result.json"
            payload = {"name": "Björn", "points": 10}

            write_json_atomic(output_file, payload)

            self.assertEqual(
                json.loads(output_file.read_text(encoding="utf-8")),
                payload,
            )
            self.assertFalse(
                output_file.with_name(f".{output_file.name}.tmp").exists()
            )


if __name__ == "__main__":
    unittest.main()
