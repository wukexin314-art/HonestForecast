import json
import tempfile
import unittest
from pathlib import Path

from honestforecast.registration import (
    RegistrationError,
    canonical_hash,
    load_registration,
    register_protocol,
    sha256_file,
    validate_audit_evidence,
    validate_registration,
    verify_assessment,
)


class RegistrationTests(unittest.TestCase):
    def _files(self, root):
        contract = root / "contract.json"
        contract.write_text(
            json.dumps(
                {
                    "study_id": "study",
                    "target_name": "target",
                    "frequency": "weekly",
                    "horizons": [1],
                    "primary_metric": "WIS",
                }
            )
        )
        protocol = root / "protocol.json"
        protocol.write_text(
            json.dumps(
                {
                    "study_id": "study",
                    "candidate": {"id": "candidate", "kind": "model"},
                    "confirmation_window": {
                        "start": "2025-01-01",
                        "end": "2025-12-31",
                    },
                    "registered_strata": [],
                    "bootstrap_repetitions": 50,
                    "seed": 7,
                    "audit_checks": ["pipeline_provenance"],
                }
            )
        )
        return contract, protocol

    def test_registration_detects_lock_and_contract_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract, protocol = self._files(root)
            lock = root / "protocol.lock.json"
            register_protocol(
                protocol, contract, lock, registered_at="2025-01-01T00:00:00Z"
            )
            self.assertEqual(load_registration(lock)["schema_version"], "1.0")
            data = json.loads(lock.read_text())
            data["protocol"]["seed"] = 8
            lock.write_text(json.dumps(data))
            with self.assertRaisesRegex(RegistrationError, "registration_sha256"):
                load_registration(lock)

    def test_assessment_settings_must_match_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract, protocol = self._files(root)
            lock = root / "protocol.lock.json"
            register_protocol(
                protocol, contract, lock, registered_at="2025-01-01T00:00:00Z"
            )
            common = {
                "path": lock,
                "contract_path": contract,
                "study_id": "study",
                "candidate_id": "candidate",
                "candidate_kind": "model",
                "strata": (),
                "bootstrap_repetitions": 50,
                "seed": 7,
                "origins": ("2025-06-01",),
            }
            validate_registration(**common)
            for change in (
                {"candidate_id": "other"},
                {"strata": ("region",)},
                {"seed": 8},
                {"origins": ("2026-01-01",)},
            ):
                with self.subTest(change=change), self.assertRaises(RegistrationError):
                    validate_registration(**{**common, **change})

    def test_audit_artifact_hash_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract, protocol = self._files(root)
            lock_path = root / "protocol.lock.json"
            register_protocol(protocol, contract, lock_path)
            artifact = root / "audit.md"
            artifact.write_text("checked\n")
            evidence = root / "evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "candidate": {"id": "candidate", "kind": "model"},
                        "checks": [
                            {
                                "id": "pipeline_provenance",
                                "status": "passed",
                                "artifact": artifact.name,
                                "sha256": sha256_file(artifact),
                            }
                        ],
                    }
                )
            )
            lock = load_registration(lock_path)
            validate_audit_evidence(
                evidence,
                registration=lock,
                candidate_id="candidate",
                candidate_kind="model",
            )
            artifact.write_text("changed\n")
            with self.assertRaisesRegex(RegistrationError, "artifact hash"):
                validate_audit_evidence(
                    evidence,
                    registration=lock,
                    candidate_id="candidate",
                    candidate_kind="model",
                )

    def test_verify_detects_output_and_input_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            source = root / "candidate.csv"
            source.write_text("value\n1\n")
            decision = {"state": "challenger", "candidate_id": "candidate"}
            robustness = bundle / "robustness.json"
            robustness.write_text(json.dumps({"decision": decision}))
            decision_log = bundle / "decision_log.jsonl"
            decision_log.write_text(json.dumps(decision) + "\n")
            other_outputs = []
            for name in ("metrics.csv", "origin_differences.csv", "evidence_card.md"):
                path = bundle / name
                path.write_text("stable\n")
                other_outputs.append(path)
            import hashlib

            def digest(path):
                return hashlib.sha256(path.read_bytes()).hexdigest()

            outputs = [robustness, decision_log, *other_outputs]
            receipt = {
                "schema_version": "3.0",
                "checks": {"protocol_registration": "passed"},
                "decision": decision,
                "input_sha256": {"candidate": digest(source)},
                "output_sha256": {path.name: digest(path) for path in outputs},
            }
            receipt["receipt_sha256"] = canonical_hash(receipt)
            (bundle / "audit_receipt.json").write_text(json.dumps(receipt))
            report = verify_assessment(bundle, input_paths={"candidate": source})
            self.assertEqual(report["status"], "verified")
            receipt_path = bundle / "audit_receipt.json"
            original_receipt = receipt_path.read_text()
            changed_receipt = json.loads(original_receipt)
            changed_receipt["decision"]["state"] = "promoted"
            receipt_path.write_text(json.dumps(changed_receipt))
            with self.assertRaisesRegex(RegistrationError, "receipt_sha256"):
                verify_assessment(bundle)
            receipt_path.write_text(original_receipt)
            source.write_text("value\n2\n")
            with self.assertRaisesRegex(RegistrationError, "input artifact"):
                verify_assessment(bundle, input_paths={"candidate": source})
            source.write_text("value\n1\n")
            robustness.write_text("{}")
            with self.assertRaisesRegex(RegistrationError, "output artifact"):
                verify_assessment(bundle)


if __name__ == "__main__":
    unittest.main()
