import csv
import json
import unittest
from pathlib import Path

from honestforecast.metrics import summarize_predictions
from honestforecast.registration import decision_code_hashes, load_registration, sha256_file


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

    def test_prospective_design_is_still_frozen(self):
        for folder in ("prospective", "prospective_v2", "prospective_v3"):
            with self.subTest(folder=folder):
                prospective = CASE / folder
                lock = load_registration(prospective / "protocol.lock.json")
                self.assertEqual(lock["input_sha256"]["contract"], sha256_file(prospective / "forecast_contract.json"))
                self.assertEqual(lock["input_sha256"]["protocol"], sha256_file(prospective / "protocol.json"))
                self.assertIn(lock["registration_sha256"], (prospective / "README.md").read_text())
        flu = ROOT / "case_studies" / "us_flu" / "confirmation"
        lock = load_registration(flu / "protocol.lock.json")
        self.assertEqual(lock["input_sha256"]["protocol"], sha256_file(flu / "protocol.json"))
        self.assertIn(lock["registration_sha256"], (flu / "README.md").read_text())
        nowcast = ROOT / "case_studies" / "us_flu_nowcast"
        readme = (nowcast / "README.md").read_text()
        for folder in ("prospective", "prospective_r2"):
            lock = load_registration(nowcast / folder / "protocol.lock.json")
            self.assertIn(lock["registration_sha256"], readme)
            self.assertEqual(lock["input_sha256"]["protocol"], sha256_file(nowcast / folder / "protocol.json"))
        # Model code is outside the lock; the README records its hashes while confirmations are open.
        for module in ("flu_nowcast.py", "flu_case.py", "dengue_case.py"):
            with self.subTest(module=module):
                self.assertIn(sha256_file(ROOT / "src" / "honestforecast" / module), readme)
        # Fails if a scoring or promotion rule is edited while the open confirmations run.
        for lock_path in (CASE / "prospective_v3" / "protocol.lock.json", nowcast / "prospective_r2" / "protocol.lock.json"):
            with self.subTest(lock=str(lock_path)):
                self.assertEqual(load_registration(lock_path)["code_sha256"], decision_code_hashes())


if __name__ == "__main__":
    unittest.main()
