import csv
import json
import unittest
from pathlib import Path

from honestforecast.metrics import summarize_predictions


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case_studies" / "india_dengue"


class CaseStudyArtifactTests(unittest.TestCase):
    def test_committed_metrics_recompute_from_predictions(self):
        receipt = json.loads((CASE / "pilot" / "pilot_receipt.json").read_text())
        for method, expected in receipt["metrics"].items():
            with (CASE / "pilot" / f"predictions_{method}.csv").open(newline="") as handle:
                actual = summarize_predictions(list(csv.DictReader(handle)))
            with self.subTest(method=method):
                for metric in ("mae", "wis", "coverage_80"):
                    self.assertAlmostEqual(actual[metric], expected[metric])

    def test_vintage_claim_is_explicitly_limited(self):
        receipt = json.loads(
            (CASE / "vintage_audit" / "audit_receipt.json").read_text()
        )
        self.assertEqual(receipt["snapshot_count"], 18)
        self.assertFalse(receipt["source_native_publication_time_proven"])


if __name__ == "__main__":
    unittest.main()
