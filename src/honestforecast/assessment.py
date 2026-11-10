"""Model-agnostic forecast feature assessment and command-line interface."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Dict, List, Mapping, Optional, Sequence

from .audit import (
    assert_common_grid,
    assert_no_future_availability,
    assert_no_future_vintage,
    case_key,
)
from .comparison import append_decision, compare_feature_family
from .contracts import ForecastContract, FeatureSpec, feature_identities, load_feature_manifest
from .evidence import render_assessment_evidence_card
from .metrics import summarize_predictions, validate_prediction_rows, weighted_interval_score


class AssessmentError(ValueError):
    """Raised when supplied study artifacts cannot support an assessment."""


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise AssessmentError(f"CSV has no header: {path}")
        rows = list(reader)
    if not rows:
        raise AssessmentError(f"CSV has no data rows: {path}")
    return rows


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise AssessmentError(f"cannot write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_contract(path: Path) -> ForecastContract:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssessmentError(f"invalid contract JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AssessmentError("forecast contract must be a JSON object")
    contract = ForecastContract.from_mapping(data)
    if contract.primary_metric.upper() != "WIS":
        raise AssessmentError("Milestone 3 decisions require primary_metric WIS")
    return contract


def _candidate_family(
    rows: Sequence[Mapping[str, object]], requested_family: Optional[str]
) -> str:
    row_families = [str(row.get("feature_family", "")).strip() for row in rows]
    if not requested_family and any(not value for value in row_families):
        raise AssessmentError(
            "candidate feature_family must be populated on every row, or pass --family"
        )
    declared = set(row_families)
    declared.discard("")
    if len(declared) > 1:
        raise AssessmentError("candidate rows must contain one feature_family")
    if requested_family and declared and requested_family not in declared:
        raise AssessmentError(
            f"--family {requested_family!r} conflicts with candidate feature_family"
        )
    family = requested_family or (next(iter(declared)) if declared else "")
    if not family:
        raise AssessmentError(
            "candidate rows require feature_family, or pass --family explicitly"
        )
    return family


def _validate_contract_horizons(
    contract: ForecastContract, rows: Sequence[Mapping[str, object]]
) -> None:
    try:
        observed = {int(row["horizon"]) for row in rows}
    except (KeyError, TypeError, ValueError) as exc:
        raise AssessmentError("prediction horizons must be integers") from exc
    expected = set(contract.horizons)
    if observed != expected:
        raise AssessmentError(
            f"prediction horizons {sorted(observed)} do not match contract {sorted(expected)}"
        )


def _family_specs(specs: Sequence[FeatureSpec], family: str) -> List[FeatureSpec]:
    selected = [spec for spec in specs if spec.family == family]
    if not selected:
        raise AssessmentError(f"candidate family {family!r} is absent from feature manifest")
    return selected


def _audit_availability(
    path: Path,
    family_specs: Sequence[FeatureSpec],
    origins: Sequence[str],
) -> Dict[str, str]:
    rows = _read_csv(path)
    required_features = {spec.feature_id for spec in family_specs}
    relevant = [
        row
        for row in rows
        if str(row.get("feature_id", "")).strip() in required_features
        and str(row.get("origin", "")).strip() in origins
    ]
    identities = [
        (str(row.get("feature_id", "")).strip(), str(row.get("origin", "")).strip())
        for row in relevant
    ]
    if len(identities) != len(set(identities)):
        raise AssessmentError("availability rows must be unique by feature_id and origin")
    missing = sorted(
        (feature_id, origin)
        for feature_id in required_features
        for origin in origins
        if (feature_id, origin) not in set(identities)
    )
    if missing:
        raise AssessmentError(
            f"availability evidence is incomplete; first missing pairs: {missing[:3]}"
        )
    assert_no_future_availability(relevant)
    checks = {"feature_availability": "passed", "feature_vintage": "not_provided"}
    vintage_values = [str(row.get("vintage_at", "")).strip() for row in relevant]
    if any(vintage_values):
        if not all(vintage_values):
            raise AssessmentError("vintage_at must be populated for every availability row")
        assert_no_future_vintage(relevant)
        checks["feature_vintage"] = "passed"
    return checks


def _origin_differences(
    baseline: Sequence[Mapping[str, object]],
    candidate: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    baseline_by_key = {case_key(row): row for row in baseline}
    candidate_by_key = {case_key(row): row for row in candidate}
    grouped: Dict[str, List[Dict[str, float]]] = {}
    for key in sorted(baseline_by_key):
        base = baseline_by_key[key]
        cand = candidate_by_key[key]
        if float(base["actual"]) != float(cand["actual"]):
            raise AssessmentError(f"actual values differ for case {key}")
        grouped.setdefault(key[0], []).append(
            {
                "wis": weighted_interval_score(cand) - weighted_interval_score(base),
                "mae": abs(float(cand["actual"]) - float(cand["point"]))
                - abs(float(base["actual"]) - float(base["point"])),
            }
        )
    return [
        {
            "origin": origin,
            "n_cases": len(values),
            "mean_wis_difference": mean(value["wis"] for value in values),
            "mean_mae_difference": mean(value["mae"] for value in values),
            "candidate_improved": mean(value["wis"] for value in values) < 0,
        }
        for origin, values in sorted(grouped.items())
    ]


def _horizon_differences(
    baseline: Sequence[Mapping[str, object]],
    candidate: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    baseline_by_key = {case_key(row): row for row in baseline}
    candidate_by_key = {case_key(row): row for row in candidate}
    grouped: Dict[int, List[float]] = {}
    for key in sorted(baseline_by_key):
        grouped.setdefault(key[2], []).append(
            weighted_interval_score(candidate_by_key[key])
            - weighted_interval_score(baseline_by_key[key])
        )
    return [
        {
            "horizon": horizon,
            "n_cases": len(values),
            "mean_wis_difference": mean(values),
        }
        for horizon, values in sorted(grouped.items())
    ]


def assess(
    *,
    contract_path: Path,
    manifest_path: Path,
    baseline_path: Path,
    candidate_path: Path,
    output_dir: Path,
    availability_path: Optional[Path] = None,
    family: Optional[str] = None,
    confirmation_frozen: bool = False,
    all_audit_gates_passed: bool = False,
    bootstrap_repetitions: int = 1000,
    seed: int = 20261109,
) -> Dict[str, object]:
    """Assess one candidate feature family against one baseline on an exact grid."""
    if bootstrap_repetitions < 20:
        raise AssessmentError("bootstrap_repetitions must be at least 20")
    contract = _load_contract(contract_path)
    specs = load_feature_manifest(manifest_path)
    baseline = validate_prediction_rows(_read_csv(baseline_path))
    candidate = validate_prediction_rows(_read_csv(candidate_path))
    assert_common_grid(baseline, candidate)
    _validate_contract_horizons(contract, baseline)
    candidate_family = _candidate_family(candidate, family)
    selected_specs = _family_specs(specs, candidate_family)
    if all_audit_gates_passed and availability_path is None:
        raise AssessmentError(
            "--all-audit-gates-passed requires origin-level --availability evidence"
        )
    if all_audit_gates_passed and any(
        spec.availability_class == "unverified" for spec in selected_specs
    ):
        raise AssessmentError("unverified feature availability cannot pass all audit gates")

    checks = {
        "forecast_contract": "passed",
        "feature_manifest": "passed",
        "prediction_schema": "passed",
        "common_grid": "passed",
        "quantile_monotonicity": "passed",
        "contract_horizons": "passed",
        "feature_availability": "not_provided",
        "feature_vintage": "not_provided",
    }
    origins = sorted({key[0] for key in (case_key(row) for row in baseline)})
    if availability_path is not None:
        checks.update(_audit_availability(availability_path, selected_specs, origins))

    decision = compare_feature_family(
        candidate_family,
        baseline,
        candidate,
        confirmation_frozen=confirmation_frozen,
        all_audit_gates_passed=all_audit_gates_passed,
        bootstrap_repetitions=bootstrap_repetitions,
        seed=seed,
    )
    baseline_metrics = summarize_predictions(baseline)
    candidate_metrics = summarize_predictions(candidate)
    metric_rows = [
        {"method": "baseline", **baseline_metrics},
        {"method": "candidate", **candidate_metrics},
    ]
    origin_rows = _origin_differences(baseline, candidate)
    robustness = {
        "decision": decision.to_dict(),
        "horizon_differences": _horizon_differences(baseline, candidate),
        "difference_sign": "candidate_minus_baseline; negative favors candidate",
    }

    input_paths = {
        "contract": Path(contract_path),
        "manifest": Path(manifest_path),
        "baseline": Path(baseline_path),
        "candidate": Path(candidate_path),
    }
    if availability_path is not None:
        input_paths["availability"] = Path(availability_path)
    receipt: Dict[str, object] = {
        "schema_version": "1.0",
        "study_id": contract.study_id,
        "candidate_family": candidate_family,
        "contract": asdict(contract),
        "feature_identities": list(feature_identities(selected_specs)),
        "input_sha256": {name: _sha256(path) for name, path in input_paths.items()},
        "checks": checks,
        "evaluation_grid": {
            "n_cases": len(baseline),
            "n_origins": len(origins),
            "horizons": sorted(contract.horizons),
        },
        "claims": {
            "confirmation_frozen": confirmation_frozen,
            "all_audit_gates_passed": all_audit_gates_passed,
            "availability_evidence_supplied": availability_path is not None,
        },
        "decision": decision.to_dict(),
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "metrics.csv", metric_rows)
    _write_csv(output_dir / "origin_differences.csv", origin_rows)
    (output_dir / "robustness.json").write_text(
        json.dumps(robustness, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "audit_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    append_decision(output_dir / "decision_log.jsonl", decision)
    (output_dir / "evidence_card.md").write_text(
        render_assessment_evidence_card(
            contract=contract,
            family_specs=selected_specs,
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            decision=decision,
            checks=checks,
            input_hashes=receipt["input_sha256"],
        ),
        encoding="utf-8",
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="honestforecast",
        description="Model-agnostic evidence checks for forecast feature admission.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    assess_parser = subparsers.add_parser(
        "assess", help="compare one candidate feature family with a baseline"
    )
    assess_parser.add_argument("--contract", type=Path, required=True)
    assess_parser.add_argument("--manifest", type=Path, required=True)
    assess_parser.add_argument("--baseline", type=Path, required=True)
    assess_parser.add_argument("--candidate", type=Path, required=True)
    assess_parser.add_argument("--availability", type=Path)
    assess_parser.add_argument("--family")
    assess_parser.add_argument("--output", type=Path, required=True)
    assess_parser.add_argument("--confirmation-frozen", action="store_true")
    assess_parser.add_argument("--all-audit-gates-passed", action="store_true")
    assess_parser.add_argument("--bootstrap-repetitions", type=int, default=1000)
    assess_parser.add_argument("--seed", type=int, default=20261109)
    args = parser.parse_args()
    try:
        receipt = assess(
            contract_path=args.contract,
            manifest_path=args.manifest,
            baseline_path=args.baseline,
            candidate_path=args.candidate,
            availability_path=args.availability,
            family=args.family,
            output_dir=args.output,
            confirmation_frozen=args.confirmation_frozen,
            all_audit_gates_passed=args.all_audit_gates_passed,
            bootstrap_repetitions=args.bootstrap_repetitions,
            seed=args.seed,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
