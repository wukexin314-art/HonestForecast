import csv
import json
import tempfile
import unittest
from pathlib import Path

from honestforecast.assessment import AssessmentError, assess
from honestforecast.audit import AuditError
from honestforecast.metrics import QUANTILE_LEVELS, quantile_column
from honestforecast.registration import register_protocol, sha256_file


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

    def _registration(
        self,
        root,
        contract,
        *,
        candidate_id,
        candidate_kind,
        strata=(),
        audit_checks=(),
    ):
        protocol = root / f"{candidate_id}-protocol.json"
        protocol.write_text(
            json.dumps(
                {
                    "study_id": "portable-example",
                    "candidate": {"id": candidate_id, "kind": candidate_kind},
                    "confirmation_window": {
                        "start": "2025-01-01",
                        "end": "2025-08-01",
                    },
                    "registered_strata": list(strata),
                    "bootstrap_repetitions": 50,
                    "seed": 20261109,
                    "audit_checks": list(audit_checks),
                }
            ),
            encoding="utf-8",
        )
        lock = root / f"{candidate_id}-protocol.lock.json"
        register_protocol(
            protocol, contract, lock, registered_at="2025-01-01T00:00:00Z"
        )
        return lock

    def _audit_evidence(self, root, candidate_id, candidate_kind):
        artifact = root / "model-audit.txt"
        artifact.write_text("training cutoff and fold-local preprocessing checked\n")
        evidence = root / "audit-evidence.json"
        evidence.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "candidate": {"id": candidate_id, "kind": candidate_kind},
                    "checks": [
                        {
                            "id": "pipeline_provenance",
                            "status": "passed",
                            "artifact": artifact.name,
                            "sha256": sha256_file(artifact),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return evidence

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
            unregistered = assess(
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
            self.assertEqual(unregistered["decision"]["state"], "challenger")
            self.assertIn("registration_missing", unregistered["decision"]["warnings"])
            registration = self._registration(
                root,
                inputs[0],
                candidate_id="digital_proxy",
                candidate_kind="feature",
            )
            receipt = assess(
                contract_path=inputs[0],
                manifest_path=inputs[1],
                baseline_path=inputs[2],
                candidate_path=inputs[3],
                availability_path=inputs[4],
                registration_path=registration,
                output_dir=root / "registered",
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

    def test_model_candidate_does_not_require_feature_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self._inputs(root)
            model_rows = _prediction_rows(1.0)
            for row in model_rows:
                row["candidate_id"] = "xgboost-v2"
                row["candidate_kind"] = "model"
            _write_csv(inputs[3], model_rows)
            output = root / "model"
            registration = self._registration(
                root,
                inputs[0],
                candidate_id="xgboost-v2",
                candidate_kind="model",
                audit_checks=("pipeline_provenance",),
            )
            audit_evidence = self._audit_evidence(root, "xgboost-v2", "model")
            receipt = assess(
                contract_path=inputs[0],
                baseline_path=inputs[2],
                candidate_path=inputs[3],
                output_dir=output,
                registration_path=registration,
                audit_evidence_path=audit_evidence,
                all_audit_gates_passed=True,
                bootstrap_repetitions=50,
            )
            self.assertEqual(receipt["candidate"], {"id": "xgboost-v2", "kind": "model"})
            self.assertEqual(receipt["checks"]["feature_manifest"], "not_required")
            self.assertEqual(receipt["decision"]["state"], "promoted")
            decision = json.loads(
                (output / "decision_log.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(decision["candidate_kind"], "model")

    def test_registered_stratum_loss_blocks_multi_unit_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self._inputs(root)
            baseline_rows = []
            candidate_rows = []
            for base, strong, weak in zip(
                _prediction_rows(5.0),
                _prediction_rows(1.0),
                _prediction_rows(6.0),
            ):
                for unit, candidate in (("north", strong), ("south", weak)):
                    baseline_row = dict(base, unit=unit, region=unit)
                    candidate_row = dict(
                        candidate,
                        unit=unit,
                        region=unit,
                        candidate_id="xgboost-v2",
                        candidate_kind="model",
                    )
                    baseline_rows.append(baseline_row)
                    candidate_rows.append(candidate_row)
            _write_csv(inputs[2], baseline_rows)
            _write_csv(inputs[3], candidate_rows)
            output = root / "strata"
            registration = self._registration(
                root,
                inputs[0],
                candidate_id="xgboost-v2",
                candidate_kind="model",
                strata=("region",),
                audit_checks=("pipeline_provenance",),
            )
            audit_evidence = self._audit_evidence(root, "xgboost-v2", "model")
            receipt = assess(
                contract_path=inputs[0],
                baseline_path=inputs[2],
                candidate_path=inputs[3],
                output_dir=output,
                strata=("region",),
                registration_path=registration,
                audit_evidence_path=audit_evidence,
                all_audit_gates_passed=True,
                bootstrap_repetitions=50,
            )
            self.assertEqual(receipt["evaluation_grid"]["n_units"], 2)
            self.assertEqual(receipt["decision"]["state"], "challenger")
            self.assertIn(
                "material_stratum_loss:region=south",
                receipt["decision"]["warnings"],
            )
            card = (output / "evidence_card.md").read_text(encoding="utf-8")
            self.assertIn("Forecast units: 2", card)
            self.assertIn("Registered strata: region", card)


if __name__ == "__main__":
    unittest.main()
