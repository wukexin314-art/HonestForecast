"""Protocol locking and assessment-bundle verification."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

from .contracts import ForecastContract


class RegistrationError(ValueError):
    """Raised when a protocol lock or evidence bundle is inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Mapping[str, object]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_object(path: Path, label: str) -> Dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistrationError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistrationError(f"{label} must be a JSON object")
    return value


def _text(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise RegistrationError(f"{label} is required")
    return text


def _date(value: object, label: str) -> str:
    text = _text(value, label)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise RegistrationError(f"{label} must be an ISO date") from exc
    return text


def _text_list(value: object, label: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RegistrationError(f"{label} must be a list")
    items = tuple(_text(item, label) for item in value)
    if len(items) != len(set(items)):
        raise RegistrationError(f"{label} must not contain duplicates")
    return items


def _normalize_protocol(data: Mapping[str, object]) -> Dict[str, object]:
    candidate = data.get("candidate")
    if not isinstance(candidate, dict):
        raise RegistrationError("protocol candidate must be an object")
    window = data.get("confirmation_window")
    if not isinstance(window, dict):
        raise RegistrationError("confirmation_window must be an object")
    start = _date(window.get("start"), "confirmation_window.start")
    end = _date(window.get("end"), "confirmation_window.end")
    if start > end:
        raise RegistrationError("confirmation_window.start must not exceed end")
    repetitions = data.get("bootstrap_repetitions", 1000)
    seed = data.get("seed", 20261109)
    if isinstance(repetitions, bool) or not isinstance(repetitions, int):
        raise RegistrationError("bootstrap_repetitions must be an integer")
    if repetitions < 20:
        raise RegistrationError("bootstrap_repetitions must be at least 20")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise RegistrationError("seed must be an integer")
    return {
        "study_id": _text(data.get("study_id"), "study_id"),
        "candidate": {
            "id": _text(candidate.get("id"), "candidate.id"),
            "kind": _text(candidate.get("kind"), "candidate.kind"),
        },
        "confirmation_window": {"start": start, "end": end},
        "registered_strata": list(
            _text_list(data.get("registered_strata", []), "registered_strata")
        ),
        "bootstrap_repetitions": repetitions,
        "seed": seed,
        "audit_checks": list(_text_list(data.get("audit_checks", []), "audit_checks")),
    }


def _load_contract(path: Path) -> ForecastContract:
    data = _read_object(path, "forecast contract")
    return ForecastContract.from_mapping(data)


# Modules whose bytes decide scores and promotion; a lock pins them so rules cannot change after registration.
# shortcut: any edit to these files (even a comment) invalidates open locks, upgrade to AST hashing if that bites.
DECISION_CODE = ("assessment.py", "audit.py", "comparison.py", "metrics.py")


def decision_code_hashes() -> Dict[str, str]:
    package = Path(__file__).resolve().parent
    return {name: sha256_file(package / name) for name in DECISION_CODE}


def register_protocol(
    protocol_path: Path,
    contract_path: Path,
    output_path: Path,
    *,
    registered_at: Optional[str] = None,
) -> Dict[str, object]:
    """Normalize and hash a protocol together with its forecast contract."""
    protocol = _normalize_protocol(_read_object(protocol_path, "protocol"))
    contract = _load_contract(contract_path)
    if protocol["study_id"] != contract.study_id:
        raise RegistrationError("protocol study_id does not match forecast contract")
    timestamp = registered_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegistrationError("registered_at must be an ISO timestamp") from exc
    lock: Dict[str, object] = {
        "schema_version": "1.1",
        "registered_at": timestamp,
        "timestamp_authority": "local_clock_untrusted",
        "protocol": protocol,
        "input_sha256": {
            "protocol": sha256_file(protocol_path),
            "contract": sha256_file(contract_path),
        },
        "code_sha256": decision_code_hashes(),
    }
    lock["registration_sha256"] = canonical_hash(lock)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return lock


def load_registration(path: Path) -> Dict[str, object]:
    lock = _read_object(path, "registration")
    digest = _text(lock.get("registration_sha256"), "registration_sha256")
    unsigned = dict(lock)
    unsigned.pop("registration_sha256", None)
    if canonical_hash(unsigned) != digest:
        raise RegistrationError("registration_sha256 does not match lock contents")
    if lock.get("schema_version") not in {"1.0", "1.1"}:
        raise RegistrationError("unsupported registration schema_version")
    timestamp = _text(lock.get("registered_at"), "registered_at")
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegistrationError("registered_at must be an ISO timestamp") from exc
    if lock.get("timestamp_authority") != "local_clock_untrusted":
        raise RegistrationError("unsupported timestamp_authority")
    protocol = lock.get("protocol")
    if not isinstance(protocol, dict) or _normalize_protocol(protocol) != protocol:
        raise RegistrationError("registration contains a non-canonical protocol")
    inputs = lock.get("input_sha256")
    if not isinstance(inputs, dict) or not isinstance(inputs.get("contract"), str):
        raise RegistrationError("registration is missing its contract hash")
    if lock["schema_version"] == "1.1" and not isinstance(lock.get("code_sha256"), dict):
        raise RegistrationError("registration is missing its decision-code hashes")
    return lock


def validate_registration(
    path: Path,
    *,
    contract_path: Path,
    study_id: str,
    candidate_id: str,
    candidate_kind: str,
    strata: Sequence[str],
    bootstrap_repetitions: int,
    seed: int,
    origins: Sequence[str],
) -> Dict[str, object]:
    """Fail if an assessment differs from its locked design."""
    lock = load_registration(path)
    protocol = lock["protocol"]
    expected = {
        "study_id": study_id,
        "candidate": {"id": candidate_id, "kind": candidate_kind},
        "registered_strata": list(dict.fromkeys(value.strip() for value in strata)),
        "bootstrap_repetitions": bootstrap_repetitions,
        "seed": seed,
    }
    for field, value in expected.items():
        if protocol[field] != value:
            raise RegistrationError(
                f"assessment {field} does not match registered protocol"
            )
    if lock["input_sha256"]["contract"] != sha256_file(contract_path):
        raise RegistrationError("forecast contract changed after registration")
    if "code_sha256" in lock:  # 1.0 locks predate code pinning
        changed = sorted(
            name for name, digest in decision_code_hashes().items()
            if lock["code_sha256"].get(name) != digest
        )
        if changed:
            raise RegistrationError(f"decision code changed after registration: {changed}")
    start = date.fromisoformat(protocol["confirmation_window"]["start"])
    end = date.fromisoformat(protocol["confirmation_window"]["end"])
    try:
        origin_dates = [(origin, date.fromisoformat(origin)) for origin in origins]
    except ValueError as exc:
        raise RegistrationError("forecast origins must be ISO dates") from exc
    outside = sorted(
        origin for origin, value in origin_dates if value < start or value > end
    )
    if outside:
        raise RegistrationError(
            f"forecast origins fall outside registered confirmation window: {outside[:3]}"
        )
    return lock


def validate_audit_evidence(
    path: Path,
    *,
    registration: Mapping[str, object],
    candidate_id: str,
    candidate_kind: str,
) -> Dict[str, Path]:
    """Validate registered audit claims and the hashes of their artifacts."""
    evidence = _read_object(path, "audit evidence")
    if evidence.get("schema_version") != "1.0":
        raise RegistrationError("unsupported audit evidence schema_version")
    if evidence.get("candidate") != {"id": candidate_id, "kind": candidate_kind}:
        raise RegistrationError("audit evidence candidate does not match assessment")
    checks = evidence.get("checks")
    if not isinstance(checks, list) or not checks:
        raise RegistrationError("audit evidence checks must be a non-empty list")
    registered_checks = registration["protocol"]["audit_checks"]
    found: Dict[str, Path] = {}
    for check in checks:
        if not isinstance(check, dict):
            raise RegistrationError("each audit check must be an object")
        check_id = _text(check.get("id"), "audit check id")
        if check_id in found:
            raise RegistrationError(f"duplicate audit check: {check_id}")
        if check.get("status") != "passed":
            raise RegistrationError(f"audit check did not pass: {check_id}")
        artifact_name = _text(check.get("artifact"), f"{check_id}.artifact")
        expected_hash = _text(check.get("sha256"), f"{check_id}.sha256")
        artifact = (Path(path).parent / artifact_name).resolve()
        if not artifact.is_file():
            raise RegistrationError(f"audit artifact is missing: {artifact_name}")
        if sha256_file(artifact) != expected_hash:
            raise RegistrationError(f"audit artifact hash mismatch: {check_id}")
        found[check_id] = artifact
    if sorted(found) != sorted(registered_checks):
        raise RegistrationError("audit evidence checks do not match registered protocol")
    return found


def verify_assessment(
    output_dir: Path,
    *,
    input_paths: Optional[Mapping[str, Path]] = None,
) -> Dict[str, object]:
    """Verify output integrity and any caller-supplied original inputs."""
    output_dir = Path(output_dir)
    receipt = _read_object(output_dir / "audit_receipt.json", "audit receipt")
    receipt_digest = _text(receipt.get("receipt_sha256"), "receipt_sha256")
    unsigned_receipt = dict(receipt)
    unsigned_receipt.pop("receipt_sha256", None)
    if canonical_hash(unsigned_receipt) != receipt_digest:
        raise RegistrationError("receipt_sha256 does not match receipt contents")
    output_hashes = receipt.get("output_sha256")
    if not isinstance(output_hashes, dict) or not output_hashes:
        raise RegistrationError("audit receipt has no output_sha256 manifest")
    for name, expected_hash in output_hashes.items():
        if Path(name).name != name:
            raise RegistrationError(f"unsafe output manifest path: {name}")
        artifact = output_dir / name
        if not artifact.is_file() or sha256_file(artifact) != expected_hash:
            raise RegistrationError(f"output artifact hash mismatch: {name}")
    robustness = _read_object(output_dir / "robustness.json", "robustness")
    decision = receipt.get("decision")
    if not isinstance(decision, dict):
        raise RegistrationError("audit receipt has no decision object")
    if robustness.get("decision") != decision:
        raise RegistrationError("robustness decision differs from audit receipt")
    log_lines = (output_dir / "decision_log.jsonl").read_text(encoding="utf-8").splitlines()
    if not log_lines:
        raise RegistrationError("decision log is empty")
    try:
        logged = json.loads(log_lines[-1])
    except json.JSONDecodeError as exc:
        raise RegistrationError("last decision log entry is invalid JSON") from exc
    if not isinstance(logged, dict):
        raise RegistrationError("last decision log entry must be an object")
    for key, value in decision.items():
        if logged.get(key) != value:
            raise RegistrationError(f"decision log differs from receipt at {key}")
    verified_inputs = []
    expected_inputs = receipt.get("input_sha256", {})
    if not isinstance(expected_inputs, dict):
        raise RegistrationError("audit receipt has no input_sha256 manifest")
    for name, path in (input_paths or {}).items():
        if name not in expected_inputs:
            raise RegistrationError(f"receipt does not declare input: {name}")
        if sha256_file(path) != expected_inputs[name]:
            raise RegistrationError(f"input artifact hash mismatch: {name}")
        verified_inputs.append(name)
    return {
        "status": "verified",
        "assessment_schema_version": receipt.get("schema_version"),
        "registration_status": receipt.get("checks", {}).get(
            "protocol_registration", "unknown"
        ),
        "outputs_verified": sorted(output_hashes),
        "inputs_verified": sorted(verified_inputs),
    }
