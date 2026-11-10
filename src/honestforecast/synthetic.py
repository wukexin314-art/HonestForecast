"""Run the Milestone 1 synthetic known-answer vertical slice."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from datetime import date
from pathlib import Path
from statistics import NormalDist
from typing import Dict, Iterable, List, Mapping, Sequence

from .audit import (
    AuditError,
    assert_common_grid,
    assert_no_future_availability,
    assert_no_future_vintage,
)
from .comparison import compare_candidate, compare_feature_family
from .dengue_case import ridge_predict
from .evidence import render_evidence_card
from .features import fit_fold_transform
from .metrics import MetricError, QUANTILE_LEVELS, quantile_column, summarize_predictions
from .screening import screen_candidates


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def _actual(month_index: int) -> float:
    seasonal = 20.0 * math.sin(2.0 * math.pi * month_index / 12.0)
    return round(100.0 + month_index + seasonal, 6)


def _row(origin_index: int, horizon: int) -> Dict[str, object]:
    target_index = origin_index + horizon
    actual = _actual(target_index)
    point = actual
    row: Dict[str, object] = {
        "origin": _add_months(date(2021, 1, 1), origin_index).isoformat(),
        "target_date": _add_months(date(2021, 1, 1), target_index).isoformat(),
        "horizon": horizon,
        "actual": actual,
        "point": point,
    }
    offsets = {0.025: -20.0, 0.1: -10.0, 0.25: -5.0, 0.5: 0.0, 0.75: 5.0, 0.9: 10.0, 0.975: 20.0}
    for level in QUANTILE_LEVELS:
        row[quantile_column(level)] = point + offsets[level]
    return row


def clean_predictions() -> List[Dict[str, object]]:
    return [_row(origin, horizon) for origin in range(24, 32) for horizon in (1, 2)]


def _shifted_predictions(errors: List[float]) -> List[Dict[str, object]]:
    rows = [_row(origin, 1) for origin in range(24, 24 + len(errors))]
    offsets = {0.025: -3.0, 0.1: -2.0, 0.25: -1.0, 0.5: 0.0, 0.75: 1.0, 0.9: 2.0, 0.975: 3.0}
    for row, error in zip(rows, errors):
        row["point"] = float(row["actual"]) + error
        for level in QUANTILE_LEVELS:
            row[quantile_column(level)] = float(row["point"]) + offsets[level]
    return rows


def null_feature_experiment(repetitions: int = 40, effect: float = 0.0) -> Dict[str, object]:
    """Compare naive post-hoc lag searching with registered/FDR screening.

    ``effect > 0`` makes lag 2 truly predictive, so the same run measures power.
    """
    naive_promotions = 0
    honest_promotions = 0
    true_lag_detections = 0
    warning_detected = False
    for seed in range(repetitions):
        generator = random.Random(9173 + seed)
        feature = [generator.gauss(0, 1) for _ in range(48)]
        target = [generator.gauss(0, 1) for _ in range(48)]
        target = [value + (effect * feature[i - 2] if i >= 2 else 0.0) for i, value in enumerate(target)]
        candidates = {}
        for lag in range(12):
            rows = []
            for index in range(lag, 48):
                rows.append(
                    {
                        "date": _add_months(date(2020, 1, 1), index).isoformat(),
                        "feature": feature[index - lag],
                        "target": target[index],
                    }
                )
            candidates[f"null_lag_{lag}"] = rows
        screened = screen_candidates(
            candidates, development_end="2023-12-01", registered_variants=3
        )
        warning_detected = warning_detected or bool(screened["multiplicity_warning"])
        if any(result["circular_pvalue"] <= 0.05 for result in screened["results"]):
            naive_promotions += 1
        if any(result["eligible"] for result in screened["results"]):
            honest_promotions += 1
        true_lag_detections += any(
            result["eligible"] and result["feature_id"] == "null_lag_2"
            for result in screened["results"]
        )
    return {
        "repetitions": repetitions,
        "effect": effect,
        "naive_promotions": naive_promotions,
        "honest_promotions": honest_promotions,
        "honest_true_lag_detections": true_lag_detections,
        "naive_false_promotion_rate": naive_promotions / repetitions,
        "honest_false_promotion_rate": honest_promotions / repetitions,
        "multiplicity_warning_detected": warning_detected,
    }


def _power_rows(series: Mapping[str, Sequence[float]], burn: int, n_origins: int, use_feature: bool) -> List[Dict[str, object]]:
    """Direct h-step ridge forecasts with Gaussian intervals from residual spread."""
    y, x = series["y"], series["x"]

    def features(s: int, h: int) -> List[float]:
        angle = 2 * math.pi * (s + h) / 12
        row = [math.sin(angle), math.cos(angle), y[s]]
        return row + [x[s + h - 2]] if use_feature else row

    rows = []
    for origin in range(burn, burn + n_origins):
        for h in (1, 2):
            train = range(2, origin - h + 1)
            point, residuals = ridge_predict(
                [features(s, h) for s in train], [y[s + h] for s in train], features(origin, h)
            )
            spread = math.sqrt(sum(r * r for r in residuals) / (len(residuals) - len(features(origin, h)) - 1))
            row = {
                "origin": _add_months(date(2021, 1, 1), origin).isoformat(),
                "target_date": _add_months(date(2021, 1, 1), origin + h).isoformat(),
                "horizon": h,
                "actual": y[origin + h],
                "point": point,
            }
            for level in QUANTILE_LEVELS:
                row[quantile_column(level)] = point + spread * NormalDist().inv_cdf(level)
            rows.append(row)
    return rows


def power_experiment(
    effects: Sequence[float] = (0.0, 0.25, 0.5, 1.0),
    origin_counts: Sequence[int] = (6, 12, 24, 36),
    repetitions: int = 100,
    bootstrap_repetitions: int = 200,
) -> List[Dict[str, object]]:
    """Release rate of a truly useful (or null) feature: naive point win vs full gate.

    ``effect`` is the feature's signal standard deviation relative to the AR noise.
    """
    burn, longest = 48, max(origin_counts)
    warning_names = (
        "event_concentration", "coverage_degradation", "fewer_than_60_percent_origins_improved",
        "uncertainty_includes_no_improvement", "material_horizon_loss",
    )
    results = {
        (e, n): {"naive": 0, "gate": 0, "warnings": dict.fromkeys(warning_names, 0)}
        for e in effects for n in origin_counts
    }
    for seed in range(repetitions):
        generator = random.Random(4100 + seed)
        x, u = [0.0], [0.0]
        for _ in range(burn + longest + 2):
            x.append(0.6 * x[-1] + 0.8 * generator.gauss(0, 1))
            u.append(0.5 * u[-1] + generator.gauss(0, 1))
        for effect in effects:
            beta = effect / math.sqrt(0.75)  # stationary sd of u is 1/sqrt(0.75)
            y = [10 + 2 * math.sin(2 * math.pi * t / 12) + u[t] + (beta * x[t - 2] if t >= 2 else 0.0) for t in range(len(u))]
            series = {"x": x, "y": y}
            base_all = _power_rows(series, burn, longest, False)
            cand_all = _power_rows(series, burn, longest, True)
            for n in origin_counts:
                decision = compare_candidate(
                    "synthetic_proxy", base_all[: 2 * n], cand_all[: 2 * n],
                    bootstrap_repetitions=bootstrap_repetitions, seed=seed,
                )
                cell = results[(effect, n)]
                cell["naive"] += decision.mean_wis_difference < 0
                cell["gate"] += decision.state == "challenger" and not decision.warnings
                for warning in decision.warnings:
                    cell["warnings"][warning] += 1
    return [
        {
            "effect": effect,
            "scored_origins": n,
            "repetitions": repetitions,
            "naive_release_rate": cell["naive"] / repetitions,
            "gate_release_rate": cell["gate"] / repetitions,
            **{f"warning_rate:{w}": c / repetitions for w, c in sorted(cell["warnings"].items())},
        }
        for (effect, n), cell in results.items()
    ]


def _expect_failure(name: str, error_type, function) -> str:
    try:
        function()
    except error_type:
        return "detected"
    raise AssertionError(f"{name} was not detected")


def run_scenarios() -> Dict[str, str]:
    clean = clean_predictions()
    summarize_predictions(clean)
    results = {"S0_clean": "passed"}
    results["S1_future_availability"] = _expect_failure(
        "future availability",
        AuditError,
        lambda: assert_no_future_availability(
            [
                {
                    "feature_id": "leaked_proxy",
                    "origin": "2023-01-01",
                    "available_at": "2023-02-01",
                }
            ]
        ),
    )
    results["S5_unequal_origins"] = _expect_failure(
        "unequal origins",
        AuditError,
        lambda: assert_common_grid(clean, clean[2:]),
    )
    crossing = [dict(row) for row in clean]
    crossing[0][quantile_column(0.025)] = crossing[0][quantile_column(0.1)] + 1.0
    results["S6_crossing_quantiles"] = _expect_failure(
        "crossing quantiles",
        MetricError,
        lambda: summarize_predictions(crossing),
    )
    results["S2_latest_revision_as_old_vintage"] = _expect_failure(
        "latest revised history substituted for an old vintage",
        AuditError,
        lambda: assert_no_future_vintage(
            [
                {
                    "feature_id": "revised_proxy",
                    "origin": "2023-01-01",
                    "vintage_at": "2024-01-01",
                }
            ]
        ),
    )
    null_experiment = null_feature_experiment()
    if not null_experiment["multiplicity_warning_detected"]:
        raise AssertionError("S3 multiplicity warning was not detected")
    if null_experiment["honest_false_promotion_rate"] > null_experiment["naive_false_promotion_rate"]:
        raise AssertionError("S3 honest false-promotion rate exceeded naive rate")
    results["S3_post_hoc_null_lags"] = "detected"
    concentrated = compare_feature_family(
        "outbreak_only",
        _shifted_predictions([20.0] + [1.0] * 7),
        _shifted_predictions([0.0] + [2.0] * 7),
        bootstrap_repetitions=200,
    )
    if "event_concentration" not in concentrated.warnings:
        raise AssertionError("S8 event concentration was not detected")
    results["S8_single_outbreak_gain"] = "detected"
    return results


def _write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    materialized = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)


def run(output_dir: Path) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions = clean_predictions()
    metrics = summarize_predictions(predictions)
    scenarios = run_scenarios()
    null_experiment = null_feature_experiment()
    feature_rows = [
        {
            "date": _add_months(date(2020, 1, 1), index).isoformat(),
            "value": None if index == 5 else float(index),
        }
        for index in range(24)
    ]
    _, lineage = fit_fold_transform(
        feature_rows,
        train_end="2021-05-01",
        output_feature_id="proxy_log1p",
        source_feature_id="proxy",
        family="synthetic_proxy",
        source_version="1",
        availability_rule="available_at <= origin",
        transform="log1p",
    )
    receipt = {
        "study_id": "synthetic-delayed-surveillance",
        "experiment_id": "milestone-2-known-answer",
        "metrics_recomputed_from_predictions": True,
        "scenario_results": scenarios,
        "null_feature_experiment": null_experiment,
        "lineage": lineage.to_dict(),
    }

    _write_csv(output_dir / "predictions.csv", predictions)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "audit_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "feature_lineage.json").write_text(
        json.dumps(lineage.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "evidence_card.md").write_text(
        render_evidence_card(
            receipt["study_id"], receipt["experiment_id"], metrics, scenarios
        ),
        encoding="utf-8",
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("build/synthetic"))
    parser.add_argument(
        "--power-repetitions", type=int, default=0,
        help="also write gate_power.csv and screening_power.csv (500 takes about 2 minutes)",
    )
    args = parser.parse_args()
    receipt = run(args.output_dir)
    if args.power_repetitions:
        _write_csv(args.output_dir / "gate_power.csv", power_experiment(repetitions=args.power_repetitions))
        _write_csv(
            args.output_dir / "screening_power.csv",
            [null_feature_experiment(args.power_repetitions, e) for e in (0.0, 0.25, 0.5, 1.0)],
        )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
