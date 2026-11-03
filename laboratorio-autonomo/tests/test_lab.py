import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab import LabError, profile_csv, write_outputs


class OfflineLabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "data.csv"
        self.source.write_text(
            "id,value,note\nA,2.0,ok\nB,,missing\nC,4.0,ok\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_profile_counts_rows_columns_and_missing_without_zero_fill(self):
        result = profile_csv(self.source)
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["column_count"], 3)
        self.assertEqual(result["columns"]["value"]["missing_count"], 1)
        self.assertEqual(result["columns"]["value"]["numeric_statistics"]["count"], 2)
        self.assertEqual(result["columns"]["value"]["numeric_statistics"]["mean"], 3.0)

    def test_hash_matches_original_bytes(self):
        expected = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.assertEqual(profile_csv(self.source)["source_sha256"], expected)

    def test_source_file_is_not_modified(self):
        before = self.source.read_bytes()
        profile_csv(self.source)
        self.assertEqual(self.source.read_bytes(), before)

    def test_outputs_are_created_and_valid_json(self):
        profile = profile_csv(self.source)
        json_path, report_path = write_outputs(profile, self.root / "out")
        self.assertTrue(json_path.is_file())
        self.assertTrue(report_path.is_file())
        self.assertEqual(json_path.read_text(encoding="utf-8").count('"source_sha256"'), 1)
        self.assertIn("Limitaciones", report_path.read_text(encoding="utf-8"))

    def test_rejects_duplicate_headers(self):
        self.source.write_text("x,x\n1,2\n", encoding="utf-8")
        with self.assertRaises(LabError):
            profile_csv(self.source)

    def test_rejects_missing_file(self):
        with self.assertRaises(LabError):
            profile_csv(self.root / "absent.csv")

    def test_non_finite_numbers_are_not_summarized_as_valid(self):
        self.source.write_text("x\n1\nNaN\n2\n", encoding="utf-8")
        result = profile_csv(self.source)
        self.assertIsNone(result["columns"]["x"]["numeric_statistics"])


if __name__ == "__main__":
    unittest.main()
