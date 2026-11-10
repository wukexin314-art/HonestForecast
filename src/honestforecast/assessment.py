"""Model-agnostic forecast change assessment and command-line interface."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from statistics import mean
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .audit import (
    assert_common_grid,
    assert_no_future_availability,
    assert_no_future_vintage,
    case_key,
)
from .comparison import append_decision, compare_candidate
from .contracts import (
    FeatureSpec,
    ForecastContract,
    feature_identities,
    load_feature_manifest,
)
from .evidence import render_assessment_evidence_card
from .metrics import summarize_predictions, validate_prediction_rows, weighted_interval_score


class AssessmentError(ValueError):
    """Raised when supplied study artifacts cannot support an assessment."""


SUPPORTED_CANDIDATE_KINDS = {
    "feature",
    "data_source",
    "model",
    "preprocessing",
    "recalibration",
    "ensemble",
    "pipeline",
}
SOURCE_CANDIDATE_KINDS = {"feature", "data_source"}


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
        raise AssessmentError("admission decisions currently require primary_metric WIS")
    return contract


def _declared_value(
    rows: Sequence[Mapping[str, object]],
    column: str,
    requested: Optional[str],
) -> Optional[str]:
    row_values = [str(row.get(column, "")).strip() for row in rows]
    declared = set(row_values)
    declared.discard("")
    if len(declared) > 1:
        raise AssessmentError(f"candidate rows must contain one {column}")
    if requested and declared and requested not in declared:
        raise AssessmentError(
            f"requested {column} {requested!r} conflicts with candidate rows"
        )
    if not requested and declared and any(not value for value in row_values):
        raise AssessmentError(
            f"candidate {column} must be populated on every row when used"
        )
    return requested or (next(iter(declared)) if declared else None)


def _candidate_identity(
    rows: Sequence[Mapping[str, object]],
    *,
    requested_id: Optional[str],
    requested_kind: Optional[str],
    legacy_family: Optional[str],
) -> Tuple[str, str]:
    if requested_id and legacy_family and requested_id != legacy_family:
        raise AssessmentError("--candidate-id conflicts with legacy --family")
    feature_family = _declared_value(rows, "feature_family", legacy_family)
    candidate_id = _declared_value(
        rows, "candidate_id", requested_id or legacy_family
    ) or feature_family
    candidate_kind = _declared_value(rows, "candidate_kind", requested_kind)
    if candidate_kind is None and feature_family:
        candidate_kind = "feature"
    if not candidate_id or not candidate_kind:
        raise AssessmentError(
            "declare candidate_id and candidate_kind in rows or command options"
        )
    if candidate_kind not in SUPPORTED_CANDIDATE_KINDS:
        raise AssessmentError(f"unsupported candidate_kind: {candidate_kind}")
    if feature_family and candidate_kind != "feature":
        raise AssessmentError(
            "legacy feature_family is only valid for candidate_kind feature"
        )
    if feature_family and candidate_kind == "feature" and feature_family != candidate_id:
        raise AssessmentError("candidate_id conflicts with legacy feature_family")
    return candidate_id, candidate_kind


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
    cases: Sequence[Tuple[str, str]],
) -> Dict[str, str]:
    rows = _read_csv(path)
    required_features = {spec.feature_id for spec in family_specs}
    relevant = [
        row
        for row in rows
        if str(row.get("feature_id", "")).strip() in required_features
        and (
            str(row.get("origin", "")).strip(),
            str(row.get("unit", "__single__")).strip(),
        )
        in cases
    ]
    identities = [
        (
            str(row.get("feature_id", "")).strip(),
            str(row.get("origin", "")).strip(),
            str(row.get("unit", "__single__")).strip(),
        )
        for row in relevant
    ]
    if len(identities) != len(set(identities)):
        raise AssessmentError(
            "availability rows must be unique by feature_id, origin, and unit"
        )
    missing = sorted(
        (feature_id, origin, unit)
        for feature_id in required_features
        for origin, unit in cases
        if (feature_id, origin, unit) not in set(identities)
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


def _stratum_differences(
    baseline: Sequence[Mapping[str, object]],
    candidate: Sequence[Mapping[str, object]],
    strata: Sequence[str],
) -> List[Dict[str, object]]:
    baseline_by_key = {case_key(row): row for row in baseline}
    candidate_by_key = {case_key(row): row for row in candidate}
    results: List[Dict[str, object]] = []
    for field in strata:
        if not field.strip():
            raise AssessmentError("stratum names must be non-empty")
        grouped: Dict[str, List[float]] = {}
        for key in sorted(baseline_by_key):
            base = baseline_by_key[key]
            cand = candidate_by_key[key]
            baseline_value = str(base.get(field, "")).strip()
            candidate_value = str(cand.get(field, "")).strip()
            if not baseline_value or not candidate_value:
                raise AssessmentError(
                    f"stratum {field!r} must be populated in both prediction files"
                )
            if baseline_value != candidate_value:
                raise AssessmentError(
                    f"stratum {field!r} differs for case {key}: "
                    f"{baseline_value!r} != {candidate_value!r}"
                )
            grouped.setdefault(baseline_value, []).append(
                weighted_interval_score(cand) - weighted_interval_score(base)
            )
        results.extend(
            {
                "stratum": field,
                "value": value,
                "n_cases": len(differences),
                "mean_wis_difference": mean(differences),
            }
            for value, differences in sorted(grouped.items())
        )
    return results


def assess(
    *,
    contract_path: Path,
    baseline_path: Path,
    candidate_path: Path,
    output_dir: Path,
    manifest_path: Optional[Path] = None,
    availability_path: Optional[Path] = None,
    family: Optional[str] = None,
    candidate_id: Optional[str] = None,
    candidate_kind: Optional[str] = None,
    strata: Sequence[str] = (),
    confirmation_frozen: bool = False,
    all_audit_gates_passed: bool = False,
    bootstrap_repetitions: int = 1000,
    seed: int = 20261109,
) -> Dict[str, object]:
    """Assess one registered forecast change against one baseline on an exact grid."""
    if bootstrap_repetitions < 20:
        raise AssessmentError("bootstrap_repetitions must be at least 20")
    contract = _load_contract(contract_path)
    baseline = validate_prediction_rows(_read_csv(baseline_path))
    candidate = validate_prediction_rows(_read_csv(candidate_path))
    assert_common_grid(baseline, candidate)
    _validate_contract_horizons(contract, baseline)
    resolved_id, resolved_kind = _candidate_identity(
        candidate,
        requested_id=candidate_id,
        requested_kind=candidate_kind,
        legacy_family=family,
    )

    checks = {
        "forecast_contract": "passed",
        "feature_manifest": "not_required",
        "prediction_schema": "passed",
        "common_grid": "passed",
        "quantile_monotonicity": "passed",
        "contract_horizons": "passed",
        "feature_availability": "not_required",
        "feature_vintage": "not_required",
    }
    selected_specs: List[FeatureSpec] = []
    registered_items: List[str] = []
    if resolved_kind in SOURCE_CANDIDATE_KINDS:
        if manifest_path is None:
            raise AssessmentError(
                f"candidate_kind {resolved_kind!r} requires --manifest"
            )
        specs = load_feature_manifest(manifest_path)
        selected_specs = _family_specs(specs, resolved_id)
        registered_items = list(feature_identities(selected_specs))
        checks.update(
            {
                "feature_manifest": "passed",
                "feature_availability": "not_provided",
                "feature_vintage": "not_provided",
            }
        )
        if all_audit_gates_passed and availability_path is None:
            raise AssessmentError(
                "source candidates require --availability to pass all audit gates"
            )
        if all_audit_gates_passed and any(
            spec.availability_class == "unverified" for spec in selected_specs
        ):
            raise AssessmentError(
                "unverified feature availability cannot pass all audit gates"
            )
    elif manifest_path is not None:
        raise AssessmentError(
            "--manifest is only valid for feature and data_source candidates"
        )
    if availability_path is not None and resolved_kind not in SOURCE_CANDIDATE_KINDS:
        raise AssessmentError(
            "--availability is only valid for feature and data_source candidates"
        )

    keys = [case_key(row) for row in baseline]
    origins = sorted({key[0] for key in keys})
    units = sorted({key[3] for key in keys})
    if availability_path is not None:
        availability_cases = sorted({(key[0], key[3]) for key in keys})
        checks.update(
            _audit_availability(availability_path, selected_specs, availability_cases)
        )

    decision = compare_candidate(
        resolved_id,
        baseline,
        candidate,
        confirmation_frozen=confirmation_frozen,
        all_audit_gates_passed=all_audit_gates_passed,
        bootstrap_repetitions=bootstrap_repetitions,
        seed=seed,
    )
    registered_strata = tuple(dict.fromkeys(value.strip() for value in strata))
    stratum_rows = _stratum_differences(baseline, candidate, registered_strata)
    stratum_warnings = tuple(
        f"material_stratum_loss:{row['stratum']}={row['value']}"
        for row in stratum_rows
        if decision.mean_wis_difference < 0 and row["mean_wis_difference"] >= 0
    )
    if stratum_warnings:
        decision = replace(
            decision,
            state="challenger" if decision.state == "promoted" else decision.state,
            warnings=decision.warnings + stratum_warnings,
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
        "stratum_differences": stratum_rows,
        "difference_sign": "candidate_minus_baseline; negative favors candidate",
    }

    input_paths = {
        "contract": Path(contract_path),
        "baseline": Path(baseline_path),
        "candidate": Path(candidate_path),
    }
    if manifest_path is not None:
        input_paths["manifest"] = Path(manifest_path)
    if availability_path is not None:
        input_paths["availability"] = Path(availability_path)
    receipt: Dict[str, object] = {
        "schema_version": "2.0",
        "study_id": contract.study_id,
        "candidate": {"id": resolved_id, "kind": resolved_kind},
        "assessment_config": {
            "bootstrap_repetitions": bootstrap_repetitions,
            "seed": seed,
            "registered_strata": list(registered_strata),
        },
        "contract": asdict(contract),
        "feature_identities": registered_items,
        "input_sha256": {name: _sha256(path) for name, path in input_paths.items()},
        "checks": checks,
        "evaluation_grid": {
            "n_cases": len(baseline),
            "n_origins": len(origins),
            "n_units": len(units),
            "horizons": sorted(contract.horizons),
        },
        "claims": {
            "confirmation_frozen": confirmation_frozen,
            "all_audit_gates_passed": all_audit_gates_passed,
            "availability_evidence_supplied": availability_path is not None,
            "registered_strata": list(registered_strata),
        },
        "decision": decision.to_dict(),
    }
    if resolved_kind == "feature":
        receipt["candidate_family"] = resolved_id

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
    append_decision(
        output_dir / "decision_log.jsonl",
        decision,
        metadata={"candidate_id": resolved_id, "candidate_kind": resolved_kind},
    )
    (output_dir / "evidence_card.md").write_text(
        render_assessment_evidence_card(
            contract=contract,
            candidate_id=resolved_id,
            candidate_kind=resolved_kind,
            registered_items=registered_items,
            registered_strata=registered_strata,
            n_units=len(units),
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
        description="Model-agnostic evidence checks for forecast change admission.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    assess_parser = subparsers.add_parser(
        "assess", help="compare one registered forecast change with a baseline"
    )
    assess_parser.add_argument("--contract", type=Path, required=True)
    assess_parser.add_argument("--manifest", type=Path)
    assess_parser.add_argument("--baseline", type=Path, required=True)
    assess_parser.add_argument("--candidate", type=Path, required=True)
    assess_parser.add_argument("--availability", type=Path)
    assess_parser.add_argument("--candidate-id")
    assess_parser.add_argument(
        "--candidate-kind", choices=sorted(SUPPORTED_CANDIDATE_KINDS)
    )
    assess_parser.add_argument("--family", help="legacy alias for a feature candidate ID")
    assess_parser.add_argument(
        "--stratum",
        action="append",
        default=[],
        help="prediction column to register for subgroup stability; repeatable",
    )
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
            candidate_id=args.candidate_id,
            candidate_kind=args.candidate_kind,
            strata=args.stratum,
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
