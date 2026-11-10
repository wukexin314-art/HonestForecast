"""US ILINet nowcast v2: Wikipedia pageviews used for their timeliness.

Changes from ``flu_case`` (v1, kept unchanged for its committed results):

1. Timeliness: at a Friday release, ILINet covers through last Saturday, but
   pageviews for Sunday-Wednesday of the current week already exist. The
   candidate uses those four days.
2. Drift: pageviews enter as log ratios (partial week vs the last full week,
   and vs the trailing 52-week mean), not as a raw level.
3. Calibration: interval spread comes from each method's own past
   out-of-sample errors, scored against values released by the origin.
4. Activity stratum (as-of wILI >= 3 at the origin) for registered subgroup gates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path
from statistics import NormalDist, mean
from typing import Dict, List, Optional, Tuple

from .comparison import compare_feature_family
from .dengue_case import ridge_predict
from .flu_case import (
    FluCaseError,
    Ledger,
    _latest_week,
    _plus_days,
    fetch as fetch_sources,
    load as load_sources,
    origins as release_origins,
    value_as_of,
)
from .metrics import QUANTILE_LEVELS, quantile_column, summarize_predictions

REFERENCE_RANGE = ("2019-07-01", "2027-09-30")
SPLITS = {"development": range(2022, 2026), "confirmation": range(2026, 2027)}
CONFIRMATION_START = "2026-11-13"  # first ILINet release after the registration push
HORIZONS = (1, 2)
TRAIN_WEEKS = 156
PARTIAL_DAYS = 4  # Sunday-Wednesday after the latest ILINet week; complete by Thursday
CALIBRATION_ERRORS = 52
MIN_ERRORS = 10
HIGH_ACTIVITY = 3.0
FEATURE_ID = "wiki_influenza_en_partial_week"
METHODS = {"ar": False, "ar_wiki_nowcast": True}
INCLUDE_LEVEL = False  # dev variant A (with trailing-year level) hurt; frozen as variant B
EXCLUDED_TRAINING: Optional[Tuple[str, str]] = None  # weeks dropped from training for both models


def load_daily(data_dir: Path) -> Dict[str, float]:
    with (Path(data_dir) / "wiki_influenza_en_daily.csv").open(newline="", encoding="utf-8") as handle:
        return {row["day"]: float(row["views"]) for row in csv.DictReader(handle)}


def wiki_features(daily: Dict[str, float], week: str) -> Optional[List[float]]:
    """Log growth of the partial next week vs week ``week``, and vs its trailing year."""
    partial = [daily.get(_plus_days(week, offset)) for offset in range(1, PARTIAL_DAYS + 1)]
    last_week = [daily.get(_plus_days(week, -offset)) for offset in range(7)]
    year = [daily.get(_plus_days(week, -offset)) for offset in range(364)]
    if None in partial or None in last_week or (INCLUDE_LEVEL and None in year):
        return None
    rate = max(mean(partial), 1.0)
    growth = math.log(rate / max(mean(last_week), 1.0))
    return [growth, math.log(rate / max(mean(year), 1.0))] if INCLUDE_LEVEL else [growth]


def _forecast(
    ledger: Ledger, daily: Dict[str, float], region: str, latest: str, horizon: int, use_wiki: bool, origin: str
) -> Optional[Tuple[float, float]]:
    def features(week: str) -> Optional[List[float]]:
        now = value_as_of(ledger, region, week, origin)
        before = value_as_of(ledger, region, _plus_days(week, -7), origin)
        if now is None or before is None:
            return None
        angle = 2 * math.pi * date.fromisoformat(_plus_days(week, 7 * horizon)).timetuple().tm_yday / 365.25
        row = [now, before, math.sin(angle), math.cos(angle)]
        if not use_wiki:
            return row
        extra = wiki_features(daily, week)
        return None if extra is None else row + extra

    train_x, train_y = [], []
    for back in range(horizon, TRAIN_WEEKS + horizon):
        week = _plus_days(latest, -7 * back)
        if EXCLUDED_TRAINING and EXCLUDED_TRAINING[0] <= week <= EXCLUDED_TRAINING[1]:
            continue
        row = features(week)
        target = value_as_of(ledger, region, _plus_days(week, 7 * horizon), origin)
        if row is not None and target is not None:
            train_x.append(row)
            train_y.append(target)
    score = features(latest)
    if score is None or len(train_y) < 30:
        return None
    point, residuals = ridge_predict(train_x, train_y, score)
    return point, math.sqrt(sum(value * value for value in residuals) / (len(residuals) - len(score) - 1))


def _season(origin: str) -> int:
    return int(origin[:4]) if origin[5:7] >= "07" else int(origin[:4]) - 1


def run(data_dir: Path, output_dir: Path, split: str) -> Dict[str, object]:
    if split not in SPLITS:
        raise FluCaseError(f"split must be one of {sorted(SPLITS)}")
    ledger, _ = load_sources(data_dir)
    daily = load_daily(data_dir)
    predictions: Dict[str, List[Dict[str, object]]] = {method: [] for method in METHODS}
    availability = []
    pending: Dict[Tuple[str, str, int], List[Tuple[str, float]]] = {}
    errors: Dict[Tuple[str, str, int], List[float]] = {}
    # Walk every origin from the first development season so calibration errors carry forward.
    for origin in release_origins(ledger, range(SPLITS["development"].start, SPLITS[split].stop)):
        for key, waiting in pending.items():
            still = []
            for target, point in waiting:
                observed = value_as_of(ledger, key[1], target, origin)
                if observed is None:
                    still.append((target, point))
                else:
                    errors.setdefault(key, []).append(observed - point)
            pending[key] = still
        in_split = _season(origin) in SPLITS[split] and (split != "confirmation" or origin >= CONFIRMATION_START)
        for region in sorted(ledger):
            latest = _latest_week(ledger, region, origin)
            if latest is None or date.fromisoformat(origin) < date.fromisoformat(_plus_days(latest, PARTIAL_DAYS + 1)):
                continue  # partial-week pageviews are not complete yet at this origin
            forecasts = {
                (method, horizon): _forecast(ledger, daily, region, latest, horizon, use_wiki, origin)
                for method, use_wiki in METHODS.items()
                for horizon in HORIZONS
            }
            if any(value is None for value in forecasts.values()):
                continue
            truths = {horizon: value_as_of(ledger, region, _plus_days(latest, 7 * horizon), None) for horizon in HORIZONS}
            score_case = in_split and all(value is not None for value in truths.values())
            activity = "high" if value_as_of(ledger, region, latest, origin) >= HIGH_ACTIVITY else "low"
            for (method, horizon), (point, spread) in forecasts.items():
                key = (method, region, horizon)
                target = _plus_days(latest, 7 * horizon)
                pending.setdefault(key, []).append((target, point))
                past = errors.get(key, [])[-CALIBRATION_ERRORS:]
                if len(past) >= MIN_ERRORS:
                    # shortcut: symmetric Gaussian with out-of-sample RMS; move to empirical quantiles if errors stay skewed.
                    spread = math.sqrt(mean(value * value for value in past))
                if not score_case:
                    continue
                row: Dict[str, object] = {
                    "origin": origin,
                    "target_date": target,
                    "horizon": horizon,
                    "unit": region,
                    "activity": activity,
                    "actual": truths[horizon],
                    "point": max(0.0, point),
                }
                for level in QUANTILE_LEVELS:
                    row[quantile_column(level)] = max(0.0, point + spread * NormalDist().inv_cdf(level))
                predictions[method].append(row)
            if score_case:
                complete = _plus_days(latest, PARTIAL_DAYS + 1)  # Wednesday's views post by Thursday
                availability.append([FEATURE_ID, origin, region, complete, complete])

    if not predictions["ar"]:
        raise FluCaseError(f"no scored cases for {split} yet")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for method, rows in predictions.items():
        with (output_dir / f"predictions_{method}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    with (output_dir / "availability.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["feature_id", "origin", "unit", "available_at", "vintage_at"])
        writer.writerows(availability)
    receipt: Dict[str, object] = {
        "study_id": "us-ilinet-wiki-nowcast",
        "split": split,
        "n_cases": len(predictions["ar"]),
        "n_origins": len({row["origin"] for row in predictions["ar"]}),
        "metrics": {method: summarize_predictions(rows) for method, rows in predictions.items()},
    }
    if split == "development":
        receipt["exploratory_decision"] = compare_feature_family(
            "wikipedia_influenza_nowcast", predictions["ar"], predictions["ar_wiki_nowcast"]
        ).to_dict()
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "run"])
    parser.add_argument("--data-dir", type=Path, default=Path("case_studies/us_flu_nowcast/data"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--split", choices=sorted(SPLITS))
    args = parser.parse_args()
    if args.command == "fetch":
        print(json.dumps(fetch_sources(args.data_dir, REFERENCE_RANGE, daily_file=True), indent=2))
    else:
        if args.output_dir is None or args.split is None:
            parser.error("run requires --output-dir and --split")
        print(json.dumps(run(args.data_dir, args.output_dir, args.split), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
