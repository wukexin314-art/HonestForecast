import csv
import json
import tempfile
import unittest
from pathlib import Path

from honestforecast.assessment import AssessmentError, assess
from honestforecast.audit import AuditError
from honestforecast.metrics import QUANTILE_LEVELS, quantile_column


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _prediction_rows(error, candidate=False):
    origins = [f"2025-{month:02d}-01" for month in range(1, 9)]
    targets = [f"2025-{month:02d}-01" for month in range(2, 10)]
    offsets = {
        0.025: -3.0,
        0.1: -2.0,
        0.25: -1.0,
        0.5: 0.0,
        0.75: 1.0,
        0.9: 2.0,
        0.975: 3.0,
    }
    rows = []
    for index, (origin, target) in enumerate(zip(origins, targets)):
        actual = 100.0 + index
        point = actual + error
        row = {
            "origin": origin,
            "target_date": target,
            "horizon": 1,
            "actual": actual,
            "point": point,
        }
        for level in QUANTILE_LEVELS:
            row[quantile_column(level)] = point + offsets[level]
        if candidate:
            row["feature_family"] = "digital_proxy"
        rows.append(row)
    return rows


class AssessmentTests(unittest.TestCase):
    def _inputs(self, root):
        contract = root / "contract.json"
        contract.write_text(
            json.dumps(
                {
                    "study_id": "portable-example",
                    "target_name": "monthly activity",
                    "frequency": "monthly",
                    "horizons": [1],
                    "primary_metric": "WIS",
                    "development_only_selection": True,
                }
            ),
            encoding="utf-8",
        )
        manifest = root / "manifest.csv"
        _write_csv(
            manifest,
            [
                {
                    "feature_id": "search_signal",
                    "family": "digital_proxy",
                    "version": "1",
                    "availability_class": "observed_with_lag",
                    "minimum_reporting_lag": "1 month",
                    "vintage_policy": "snapshot_every_fetch",
                    "state": "candidate",
                }
            ],
        )
        baseline = root / "baseline.csv"
        candidate = root / "candidate.csv"
        baseline_rows = _prediction_rows(5.0)
        candidate_rows = _prediction_rows(1.0, candidate=True)
        _write_csv(baseline, baseline_rows)
        _write_csv(candidate, candidate_rows)
        availability = root / "availability.csv"
        _write_csv(
            availability,
            [
                {
                    "feature_id": "search_signal",
                    "origin": row["origin"],
                    "available_at": row["origin"],
                    "vintage_at": row["origin"],
                }
                for row in candidate_rows
            ],
        )
        return contract, manifest, baseline, candidate, availability

    def test_end_to_end_assessment_writes_portable_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self._inputs(root)
            output = root / "result"
            receipt = assess(
                contract_path=inputs[0],
                manifest_path=inputs[1],
                baseline_path=inputs[2],
                candidate_path=inputs[3],
                availability_path=inputs[4],
                output_dir=output,
                bootstrap_repetitions=50,
            )
            self.assertEqual(receipt["decision"]["state"], "challenger")
            self.assertEqual(receipt["checks"]["feature_availability"], "passed")
            self.assertEqual(receipt["evaluation_grid"]["n_origins"], 8)
            for name in (
                "audit_receipt.json",
                "metrics.csv",
                "origin_differences.csv",
                "robustness.json",
                "decision_log.jsonl",
                "evidence_card.md",
            ):
                self.assertTrue((output / name).is_file(), name)
            self.assertIn(
                "Decision state: `challenger`",
                (output / "evidence_card.md").read_text(encoding="utf-8"),
            )

    def test_promotion_requires_availability_and_explicit_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self._inputs(root)
            with self.assertRaises(AssessmentError):
                assess(
                    contract_path=inputs[0],
                    manifest_path=inputs[1],
                    baseline_path=inputs[2],
                    candidate_path=inputs[3],
                    output_dir=root / "missing-evidence",
                    all_audit_gates_passed=True,
                    bootstrap_repetitions=50,
                )
            receipt = assess(
                contract_path=inputs[0],
                manifest_path=inputs[1],
                baseline_path=inputs[2],
                candidate_path=inputs[3],
                availability_path=inputs[4],
                output_dir=root / "promoted",
                confirmation_frozen=True,
                all_audit_gates_passed=True,
                bootstrap_repetitions=50,
            )
            self.assertEqual(receipt["decision"]["state"], "promoted")

    def test_future_availability_and_unequal_grids_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self._inputs(root)
            with inputs[4].open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["available_at"] = "2026-01-01"
            _write_csv(inputs[4], rows)
            with self.assertRaises(AuditError):
                assess(
                    contract_path=inputs[0],
                    manifest_path=inputs[1],
                    baseline_path=inputs[2],
                    candidate_path=inputs[3],
                    availability_path=inputs[4],
                    output_dir=root / "future",
                    bootstrap_repetitions=50,
                )
            with inputs[3].open(newline="", encoding="utf-8") as handle:
                candidate_rows = list(csv.DictReader(handle))
            _write_csv(inputs[3], candidate_rows[:-1])
            with self.assertRaises(AuditError):
                assess(
                    contract_path=inputs[0],
                    manifest_path=inputs[1],
                    baseline_path=inputs[2],
                    candidate_path=inputs[3],
                    output_dir=root / "grid",
                    bootstrap_repetitions=50,
                )


if __name__ == "__main__":
    unittest.main()
