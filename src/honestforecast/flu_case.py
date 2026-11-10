"""US ILINet wILI case study with source-native release vintages from Delphi.

``fetch`` stores Delphi's V5 archive for ILINet wILI (one row per value change,
stamped with its real release date) and weekly English Wikipedia
"Influenza" pageviews from the Wikimedia REST API. ``run`` replays every weekly release as a forecast
origin, so as-of and latest-revised inputs come from the same ledger.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import io
import json
import math
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from statistics import NormalDist
from typing import Dict, List, Optional, Sequence, Tuple

from .comparison import compare_feature_family
from .dengue_case import ridge_predict
from .metrics import QUANTILE_LEVELS, quantile_column, summarize_predictions

ARCHIVE = "https://delphi.cmu.edu/epidata/v5/archive/"
PAGEVIEWS = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/user/Influenza/daily/{start}/{end}"
)
REFERENCE_RANGE = ("2019-07-01", "2026-09-30")
# Seasons 2020/21-2021/22 are COVID-disrupted, so they serve only as training history.
SPLITS = {"development": range(2022, 2024), "confirmation": range(2024, 2026)}
HORIZONS = (1, 2)
TRAIN_WEEKS = 156
FEATURE_ID = "wiki_influenza_en"

# region -> week-ending Saturday (ISO) -> (sorted release dates, values)
Ledger = Dict[str, Dict[str, Tuple[List[str], List[float]]]]


class FluCaseError(ValueError):
    """Raised when the flu case cannot be reproduced."""


def _plus_days(day: str, days: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=days)).isoformat()


def _open(url: str):
    # Wikimedia requires a descriptive User-Agent; it carries no personal data.
    request = urllib.request.Request(url, headers={"User-Agent": "HonestForecast-research/0.7 (python urllib)"})
    for _ in range(5):
        try:
            return urllib.request.urlopen(request, timeout=300)
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            # Anonymous Delphi access is rate limited per hour; wait as long as the server asks.
            time.sleep(int(exc.headers.get("Retry-After", "600")) + 5)
    raise FluCaseError(f"still rate limited after 5 waits: {url}")


def fetch(data_dir: Path, reference_range: Tuple[str, str] = REFERENCE_RANGE, daily_file: bool = False) -> Dict[str, int]:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    first, last = reference_range
    changes = []
    for geo_type in ("nation", "hhs"):
        url = (
            f"{ARCHIVE}?source=fluview_ilinet&signal=wili&geo_type={geo_type}&limit=-1"
            "&columns=report_time,geo_value,reference_time,value"
        )
        with _open(url) as response:
            for row in csv.DictReader(io.TextIOWrapper(response, encoding="utf-8")):
                if first <= row["reference_time"] <= last and row["value"] not in ("", "NA"):
                    region = "nat" if geo_type == "nation" else f"hhs{row['geo_value']}"
                    changes.append([region, row["reference_time"], row["report_time"][:10], round(float(row["value"]), 5)])
    with (data_dir / "fluview_wili_revisions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["region", "reference_saturday", "released", "wili"])
        writer.writerows(sorted(changes))
    url = PAGEVIEWS.format(start=first.replace("-", ""), end=last.replace("-", ""))
    with _open(url) as response:
        daily = json.load(response).get("items") or []
    weeks: Dict[str, List[int]] = {}
    for item in daily:
        day = date(int(item["timestamp"][:4]), int(item["timestamp"][4:6]), int(item["timestamp"][6:8]))
        saturday = day + timedelta(days=(5 - day.weekday()) % 7)  # MMWR weeks run Sunday-Saturday
        weeks.setdefault(saturday.isoformat(), []).append(int(item["views"]))
    complete = sorted((week, sum(views)) for week, views in weeks.items() if len(views) == 7)
    if daily_file:
        with (data_dir / "wiki_influenza_en_daily.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["day", "views"])
            writer.writerows(
                sorted((f"{item['timestamp'][:4]}-{item['timestamp'][4:6]}-{item['timestamp'][6:8]}", int(item["views"])) for item in daily)
            )
    if not complete:
        raise FluCaseError("pageview API returned no complete weeks")
    with (data_dir / "wiki_influenza_en.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["reference_saturday", "views"])
        writer.writerows(complete)
    return {"revision_rows": len(changes), "wiki_weeks": len(complete)}


def load(data_dir: Path) -> Tuple[Ledger, Dict[str, float]]:
    ledger: Ledger = {}
    with (Path(data_dir) / "fluview_wili_revisions.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):  # sorted by region, week, release
            released, values = ledger.setdefault(row["region"], {}).setdefault(row["reference_saturday"], ([], []))
            released.append(row["released"])
            values.append(float(row["wili"]))
    with (Path(data_dir) / "wiki_influenza_en.csv").open(newline="", encoding="utf-8") as handle:
        wiki = {row["reference_saturday"]: float(row["views"]) for row in csv.DictReader(handle)}
    return ledger, wiki


def value_as_of(ledger: Ledger, region: str, week: str, as_of: Optional[str]) -> Optional[float]:
    """Latest value released on or before ``as_of``; ``None`` means latest revised."""
    entry = ledger.get(region, {}).get(week)
    if entry is None:
        return None
    released, values = entry
    position = len(released) if as_of is None else bisect.bisect_right(released, as_of)
    return values[position - 1] if position else None


def origins(ledger: Ledger, seasons: Sequence[int]) -> List[str]:
    """National release dates from October through May of each season."""
    releases = sorted({day for released, _ in ledger["nat"].values() for day in released})
    windows = [(f"{season}-10-01", f"{season + 1}-05-31") for season in seasons]
    return [day for day in releases if any(start <= day <= end for start, end in windows)]


def _latest_week(ledger: Ledger, region: str, as_of: str) -> Optional[str]:
    weeks = [week for week, (released, _) in ledger.get(region, {}).items() if released[0] <= as_of]
    return max(weeks) if weeks else None


def _forecast(
    ledger: Ledger, wiki: Dict[str, float], region: str, latest: str, horizon: int,
    use_wiki: bool, vintage: Optional[str],
) -> Optional[Tuple[float, float]]:
    """Direct ridge forecast of wILI ``horizon`` weeks after ``latest``; returns (point, residual sd)."""

    def features(week: str) -> Optional[List[float]]:
        now = value_as_of(ledger, region, week, vintage)
        before = value_as_of(ledger, region, _plus_days(week, -7), vintage)
        if now is None or before is None or (use_wiki and week not in wiki):
            return None
        angle = 2 * math.pi * date.fromisoformat(_plus_days(week, 7 * horizon)).timetuple().tm_yday / 365.25
        row = [now, before, math.sin(angle), math.cos(angle)]
        return row + [math.log1p(wiki[week])] if use_wiki else row

    train_x, train_y = [], []
    for back in range(horizon, TRAIN_WEEKS + horizon):
        week = _plus_days(latest, -7 * back)
        row = features(week)
        target = value_as_of(ledger, region, _plus_days(week, 7 * horizon), vintage)
        if row is not None and target is not None:
            train_x.append(row)
            train_y.append(target)
    score = features(latest)
    if score is None or len(train_y) < 30:
        return None
    point, residuals = ridge_predict(train_x, train_y, score)
    spread = math.sqrt(sum(value * value for value in residuals) / (len(residuals) - len(score) - 1))
    return point, spread


METHODS = {
    "ar": (False, "as_of"),
    "ar_wiki": (True, "as_of"),
    "ar_latest_revised": (False, "latest"),
    "ar_wiki_latest_revised": (True, "latest"),
}


def run(data_dir: Path, output_dir: Path, split: str) -> Dict[str, object]:
    if split not in SPLITS:
        raise FluCaseError(f"split must be one of {sorted(SPLITS)}")
    ledger, wiki = load(data_dir)
    predictions: Dict[str, List[Dict[str, object]]] = {method: [] for method in METHODS}
    availability = []
    for origin in origins(ledger, SPLITS[split]):
        for region in sorted(ledger):
            latest = _latest_week(ledger, region, origin)
            if latest is None:
                continue
            forecasts, truths = {}, {}
            for horizon in HORIZONS:
                truths[horizon] = value_as_of(ledger, region, _plus_days(latest, 7 * horizon), None)
                for method, (use_wiki, kind) in METHODS.items():
                    forecasts[method, horizon] = _forecast(
                        ledger, wiki, region, latest, horizon, use_wiki, origin if kind == "as_of" else None
                    )
            # Score only cases every method can produce, so all grids match exactly.
            if any(value is None for value in list(forecasts.values()) + list(truths.values())):
                continue
            for (method, horizon), (point, spread) in forecasts.items():
                row: Dict[str, object] = {
                    "origin": origin,
                    "target_date": _plus_days(latest, 7 * horizon),
                    "horizon": horizon,
                    "unit": region,
                    "actual": truths[horizon],
                    "point": max(0.0, point),
                }
                for level in QUANTILE_LEVELS:
                    row[quantile_column(level)] = max(0.0, point + spread * NormalDist().inv_cdf(level))
                predictions[method].append(row)
            # Daily pageviews post within a day, so the week is complete by Monday; never revised.
            available = _plus_days(latest, 2)
            availability.append([FEATURE_ID, origin, region, available, available])

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for method, rows in predictions.items():
        if not rows:
            raise FluCaseError(f"no scored cases for {split}")
        with (output_dir / f"predictions_{method}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    with (output_dir / "availability.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["feature_id", "origin", "unit", "available_at", "vintage_at"])
        writer.writerows(availability)
    metrics = {method: summarize_predictions(rows) for method, rows in predictions.items()}
    receipt: Dict[str, object] = {
        "study_id": "us-ilinet-wiki",
        "split": split,
        "seasons": [f"{season}/{season + 1}" for season in SPLITS[split]],
        "n_cases": len(predictions["ar"]),
        "n_origins": len({row["origin"] for row in predictions["ar"]}),
        "metrics": metrics,
        "vintage_optimism_wis": {
            "ar": metrics["ar_latest_revised"]["wis"] - metrics["ar"]["wis"],
            "ar_wiki": metrics["ar_wiki_latest_revised"]["wis"] - metrics["ar_wiki"]["wis"],
        },
    }
    if split == "development":  # exploratory; confirmation goes only through the registered assess CLI
        receipt["exploratory_decision"] = compare_feature_family(
            "wikipedia_influenza", predictions["ar"], predictions["ar_wiki"]
        ).to_dict()
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "run"])
    parser.add_argument("--data-dir", type=Path, default=Path("case_studies/us_flu/data"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--split", choices=sorted(SPLITS))
    args = parser.parse_args()
    if args.command == "fetch":
        print(json.dumps(fetch(args.data_dir), indent=2))
    else:
        if args.output_dir is None or args.split is None:
            parser.error("run requires --output-dir and --split")
        print(json.dumps(run(args.data_dir, args.output_dir, args.split), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
