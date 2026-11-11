"""Out-of-period replication of McDonald et al. (2021, PNAS): AR3 quantile regression plus auxiliary indicators.

Frozen specification: see PROTOCOL_DRAFT.md. Needs numpy and scipy (case study only; the package stays stdlib).

    python replicate.py fetch --split development
    python replicate.py run --split development --data asof
"""

from __future__ import annotations

import argparse
import csv
import functools
import gzip
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import linprog

API = "https://api.delphi.cmu.edu/epidata/covidcast/"
CACHE = Path(__file__).resolve().parents[2] / "build" / "covid_cache"
KEY_FILE = Path.home() / ".config" / "delphi" / "key"  # private, outside the repository
TARGET = ("jhu-csse", "confirmed_7dav_incidence_prop")
COUNT = ("jhu-csse", "confirmed_7dav_incidence_num")
INDICATORS = {
    "chng_cli": ("chng", "smoothed_adj_outpatient_cli"),
    "chng_covid": ("chng", "smoothed_adj_outpatient_covid"),
    "dv_cli": ("doctor-visits", "smoothed_adj_cli"),
    "ctis_cmnty_cli": ("fb-survey", "smoothed_hh_cmnty_cli"),
    "gs_anosmia_ageusia": ("google-symptoms", "sum_anosmia_ageusia_smoothed_search"),
}
SIGNALS = {"y": TARGET, "count": COUNT, **INDICATORS}
ZERO_IMPUTE = {"gs_anosmia_ageusia"}  # as AR3GSSAA3_Zero
CHNG = {"chng_cli", "chng_covid"}
TAUS = (0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975)
HORIZONS = (7, 14, 21)
LAGS = (0, 7, 14)
NTRAIN = 21
LOOKBACK = 62  # days of history per snapshot, as download_signals.R
CASE_FLOOR = 30
SPLITS = {
    "development": (date(2020, 6, 15), date(2020, 12, 28)),
    "confirmation": (date(2021, 4, 5), date(2022, 1, 17)),
}


def forecast_dates(split: str):
    """Every day from the split's first Monday through the last complete Monday-Sunday week."""
    start, end = SPLITS[split]
    day = start
    while week_of(day) <= end:
        yield day
        day += timedelta(days=1)


def week_of(day: date) -> date:
    """Resampling unit: the Sunday ending the forecast week. Daily origins share targets for up to
    21 days, so the bootstrap resamples weeks (blocks of round(41^(1/3)) = 3 weeks) rather than days."""
    return day + timedelta(days=6 - day.weekday())


def _ymd(day: date) -> str:
    return day.strftime("%Y%m%d")


def _parse(value: int) -> date:
    text = str(value)
    return date(int(text[:4]), int(text[4:6]), int(text[6:]))


_last_call = [0.0]


def _query(params: dict, path: Path) -> list:
    """Cached Delphi query. Without DELPHI_EPIDATA_KEY, calls are spaced to stay under the anonymous limit."""
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    key = os.environ.get("DELPHI_EPIDATA_KEY") or (KEY_FILE.read_text().strip() if KEY_FILE.exists() else None)
    if key:
        params = {**params, "api_key": key}
    else:
        time.sleep(max(0.0, 62 - (time.time() - _last_call[0])))
    for attempt in range(6):
        try:
            _last_call[0] = time.time()
            with urllib.request.urlopen(API + "?" + urllib.parse.urlencode(params), timeout=300) as response:
                payload = json.load(response)
            break
        except urllib.error.HTTPError as error:
            if attempt == 5 or error.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(int(error.headers.get("retry-after", 60)) + 5)
    if payload.get("result") not in (1, -2):  # -2 = no results, a valid empty answer
        raise RuntimeError(f"{params.get('data_source')}/{params.get('signals')}: {payload.get('message')}")
    rows = [[r["geo_value"], r["time_value"], r["value"], r["issue"]] for r in payload.get("epidata") or []]
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(rows).encode()))
    print("fetched", path.name, len(rows), flush=True)
    return rows


def _base(source, signal, start, end):
    return dict(data_source=source, signals=signal, time_type="day", geo_type="hrr",
                time_values=f"{_ymd(start)}-{_ymd(end)}", geo_values="*")


def fetch_latest(source: str, signal: str, start: date, end: date) -> list:
    """Current (finalized) values."""
    return _query(_base(source, signal, start, end), CACHE / f"{source}__{signal}__{_ymd(start)}_{_ymd(end)}__latest.json.gz")


def fetch_history(source: str, signal: str, start: date, end: date) -> list:
    """Issues for time values in [start, end], in 31-day chunks.

    An origin reads a cell only if the cell is within LOOKBACK days before it, so issues later
    than LOOKBACK days after a chunk's last day can never be the as-of value and are not fetched."""
    rows, chunk = [], start
    while chunk <= end:
        stop = min(end, chunk + timedelta(days=30))
        last_issue = min(end, stop + timedelta(days=LOOKBACK))
        params = {**_base(source, signal, chunk, stop), "issues": f"{_ymd(chunk)}-{_ymd(last_issue)}"}
        rows += _query(params, CACHE / f"{source}__{signal}__{_ymd(chunk)}_{_ymd(stop)}__issues_{_ymd(last_issue)}.json.gz")
        chunk = stop + timedelta(days=1)
    return rows


def _table(rows) -> dict:
    return {(geo, _parse(t)): (value, _parse(issue)) for geo, t, value, issue in rows if value is not None}


@functools.lru_cache(maxsize=None)
def _history_index(split: str, key: str) -> dict:
    """time value -> {geo: issue-sorted [(issue, value)]} over the split's look-back range."""
    start, end = SPLITS[split]
    index: dict = {}
    for geo, t, value, issue in fetch_history(*SIGNALS[key], start - timedelta(days=LOOKBACK), end):
        index.setdefault(_parse(t), {}).setdefault(geo, []).append((_parse(issue), value))
    for by_geo in index.values():
        for versions in by_geo.values():
            versions.sort()
    return index


@functools.lru_cache(maxsize=None)
def _finalized(split: str, key: str) -> dict:
    start, end = SPLITS[split]
    return _table(fetch_latest(*SIGNALS[key], start - timedelta(days=LOOKBACK), end))


def snapshot(origin: date, finalized: bool = False) -> dict:
    """What the Delphi API would return with as_of=origin, rebuilt from the issue history.

    With finalized=True, values are replaced by finalized ones on the same (geo, date) cells, so
    latency is unchanged and only revisions differ."""
    split, start = _split_of(origin), origin - timedelta(days=LOOKBACK - 1)
    out = {}
    for key in SIGNALS:
        table, index = {}, _history_index(split, key)
        for offset in range(LOOKBACK):
            t = start + timedelta(days=offset)
            for geo, versions in index.get(t, {}).items():
                known = [v for v in versions if v[0] <= origin]
                if known and known[-1][1] is not None:
                    table[(geo, t)] = (known[-1][1], known[-1][0])
        if finalized:
            final = _finalized(split, key)
            table = {k: (final[k][0], v[1]) for k, v in table.items() if k in final}
        out[key] = table
    return out


def _value(table, geo, day, impute):
    hit = table.get((geo, day))
    return hit[0] if hit else (0.0 if impute else None)


def _latest(table, geo):
    days = [d for (g, d) in table if g == geo]
    return max(days) if days else None


def _fit_quantiles(x: np.ndarray, y: np.ndarray, newx: np.ndarray) -> np.ndarray:
    """Unpenalised linear quantile regression (lambda = 0), solved exactly as an LP."""
    n, p = x.shape
    eye = sparse.identity(n, format="csr")
    a_eq = sparse.hstack([sparse.csr_matrix(x), sparse.csr_matrix(-x), eye, -eye], format="csr")
    bounds = [(0, None)] * (2 * p + 2 * n)
    preds = []
    for tau in TAUS:
        cost = np.concatenate([np.zeros(2 * p), tau * np.ones(n), (1 - tau) * np.ones(n)])
        result = linprog(cost, A_eq=a_eq, b_eq=y, bounds=bounds, method="highs")
        if not result.success:
            raise RuntimeError(result.message)
        beta = result.x[:p] - result.x[p:2 * p]
        preds.append(newx @ beta)
    return np.sort(np.array(preds).T, axis=1)  # post hoc sorting, as the paper


def _rows(data, geos, model, end, impute, horizon):
    train_x, train_y = [], []
    for geo in geos:
        for offset in range(NTRAIN):
            t = end - timedelta(days=offset)
            response = _value(data["y"], geo, t + timedelta(days=horizon), False)
            features = [_value(data["y"], geo, t - timedelta(days=lag), False) for lag in LAGS]
            if model != "ar3":
                features += [_value(data[model], geo, t - timedelta(days=lag), impute) for lag in LAGS]
            if response is None or any(v is None for v in features):
                continue
            train_x.append([1.0] + features)
            train_y.append(response)
    return np.array(train_x), np.array(train_y)


def forecast_origin(args):
    origin, mode = args
    data = snapshot(origin, finalized=mode == "finalized")
    geos = sorted({g for (g, _) in data["y"]})
    out = {}
    chng_ok = sum(1 for g in geos if (_latest(data["chng_cli"], g) or date.min) >= origin - timedelta(days=14)) >= 0.9 * len(geos)
    meta = {}
    for geo in geos:
        last = _latest(data["y"], geo)
        count = _value(data["count"], geo, last, False) if last else None
        now, before = (_value(data["y"], geo, last, False), _value(data["y"], geo, last - timedelta(days=7), False)) if last else (None, None)
        if now is None or before is None:
            continue
        change = (now / before - 1) if before > 0 else (1.0 if now > 0 else 0.0)
        trend = "rising" if change > 0.1 else "falling" if change < -0.1 else "flat"
        meta[geo] = (last, count, trend)
    last_y = max(d for (_, d) in data["y"])
    out["flatline"] = []  # development sanity check only: latest value plus symmetrised pooled h-day changes
    for horizon in HORIZONS:
        x, y = _rows(data, geos, "ar3", last_y - timedelta(days=horizon), False, horizon)
        if len(y) < 50:
            continue
        changes = np.concatenate([y - x[:, 1], x[:, 1] - y])
        offsets = np.quantile(changes, TAUS)
        for geo, (last, count, trend) in meta.items():
            if count is None or count < CASE_FLOOR:
                continue
            out["flatline"].append((geo, horizon, trend, None, data["y"][(geo, last)][0] + offsets))
    for model in ["ar3", *INDICATORS]:
        if model in CHNG and not chng_ok:
            out[model] = []
            continue
        impute = model in ZERO_IMPUTE
        rows = []
        for horizon in HORIZONS:
            end = last_y - timedelta(days=horizon)
            if model != "ar3":
                feature_days = [d for (_, d) in data[model]]
                if not feature_days:
                    continue
                end = min(end, max(feature_days))
            x, y = _rows(data, geos, model, end, impute, horizon)
            if len(y) < 50:
                continue
            new, keys = [], []
            for geo, (last, count, trend) in meta.items():
                if count is None or count < CASE_FLOOR:
                    continue
                features = [_value(data["y"], geo, last - timedelta(days=lag), False) for lag in LAGS]
                available = None
                if model != "ar3":
                    flast = _latest(data[model], geo)
                    if flast is None and not impute:
                        continue
                    if flast is not None:
                        features += [_value(data[model], geo, flast - timedelta(days=lag), impute) for lag in LAGS]
                        available = data[model][(geo, flast)][1]
                    else:
                        features += [0.0, 0.0, 0.0]
                        available = "imputed"  # no value known at the origin; the zero is decided then
                if any(v is None for v in features):
                    continue
                new.append([1.0] + features)
                keys.append((geo, trend, available))
            if not new:
                continue
            preds = _fit_quantiles(x, y, np.array(new))
            for (geo, trend, available), q in zip(keys, preds):
                rows.append((geo, horizon, trend, available, q))
        out[model] = rows
    return origin, out


def _split_of(origin: date) -> str:
    return next(s for s, (a, b) in SPLITS.items() if a <= origin <= b)


def run(split: str, mode: str, output: Path, workers: int) -> None:
    origins = list(forecast_dates(split))
    start, end = SPLITS[split]
    truth = _table(fetch_latest(*TARGET, start, end + timedelta(days=max(HORIZONS))))
    for key in SIGNALS:  # fetch serially before forking, so workers only read the cache
        fetch_history(*SIGNALS[key], start - timedelta(days=LOOKBACK), end)
        if mode == "finalized":
            fetch_latest(*SIGNALS[key], start - timedelta(days=LOOKBACK), end)
    output.mkdir(parents=True, exist_ok=True)
    header = ["origin", "forecast_date", "target_date", "horizon", "unit", "trend", "actual", "point"] + [f"q{t:g}" for t in TAUS]
    files = {m: open(output / f"predictions_{m}.csv", "w", newline="") for m in ["flatline", "ar3", *INDICATORS]}
    writers = {m: csv.writer(f) for m, f in files.items()}
    for w in writers.values():
        w.writerow(header)
    coverage, latest_available, imputed = {}, {}, {}
    with ProcessPoolExecutor(workers) as pool:
        for origin, out in pool.map(forecast_origin, [(o, mode) for o in origins]):
            for model, rows in out.items():
                coverage.setdefault(model, []).append(len(rows))
                for geo, horizon, trend, available, q in rows:
                    target = origin + timedelta(days=horizon)
                    actual = truth.get((geo, target))
                    if actual is None:
                        continue
                    week = week_of(origin)
                    writers[model].writerow([week, origin, target, horizon, geo, trend, actual[0], q[3], *q])
                    if model in INDICATORS:
                        # the imputed zero is decided at the forecast date from what is known then
                        used = origin if available == "imputed" else available
                        imputed[model] = imputed.get(model, 0) + (available == "imputed")
                        key = (model, week, geo)
                        latest_available[key] = max(latest_available.get(key, (used, origin)), (used, origin))
            print(origin, {m: len(r) for m, r in out.items()}, flush=True)
    for f in files.values():
        f.close()
    with (output / "availability.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)  # per week and unit: the latest source date used on any day of that week
        writer.writerow(["feature_id", "origin", "unit", "available_at", "vintage_at"])
        for (model, week, geo), (used, origin) in sorted(latest_available.items()):
            writer.writerow([model, week, geo, used, origin])
    (output / "receipt.json").write_text(json.dumps({
        "split": split, "data": mode, "forecast_dates": [str(o) for o in origins],
        "resampling_unit": "forecast week, labelled by its Sunday (origin column)",
        "cases_per_forecast_date": coverage, "zero_imputed_cases": imputed,
        "truth": "Delphi latest values as fetched",
    }, indent=1))


def check_snapshots() -> None:
    """Assert that snapshots rebuilt from issue history equal the API's own as_of answers."""
    names = {sig: key for key, sig in SIGNALS.items()}
    checked = 0
    for path in sorted(CACHE.glob("*__*__*_*__[0-9]*.json.gz")):
        source, signal, span, tag = path.name[: -len(".json.gz")].split("__")
        origin = _parse(int(tag))
        if span.split("_")[1] != tag or (source, signal) not in names:
            continue
        expected = _table(json.loads(gzip.decompress(path.read_bytes())))
        rebuilt = snapshot(origin)[names[(source, signal)]]
        assert rebuilt == expected, (path.name, len(rebuilt), len(expected),
                                     next((k for k in expected if rebuilt.get(k) != expected[k]), None))
        checked += 1
    assert checked, "no direct as_of snapshots cached to compare against"
    print(f"{checked} rebuilt snapshots match the API's as_of answers exactly")


def prepare(output: Path, destination: Path) -> None:
    """Pair each indicator with AR3 on the cases both produced (registered rule), logging every drop."""
    def load(name):
        with (output / f"predictions_{name}.csv").open(newline="") as handle:
            return {(r["origin"], r["target_date"], r["horizon"], r["unit"]): r for r in csv.DictReader(handle)}

    with (output / "availability.csv").open(newline="") as handle:
        availability = list(csv.DictReader(handle))
    baseline = load("ar3")
    planned = len({week_of(d) for d in forecast_dates(_split_of(date.fromisoformat(next(iter(baseline.values()))["forecast_date"])))})
    log = {}
    for model in INDICATORS:
        candidate = load(model)
        keys = sorted(set(baseline) & set(candidate))
        folder = destination / model
        folder.mkdir(parents=True, exist_ok=True)
        for name, rows in (("baseline", baseline), ("candidate", candidate)):
            with (folder / f"{name}.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(next(iter(rows.values())).keys()))
                writer.writeheader()
                writer.writerows(rows[k] for k in keys)
        scored = {(k[0], k[3]) for k in keys}
        with (folder / "availability.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(availability[0].keys()))
            writer.writeheader()
            writer.writerows(r for r in availability if r["feature_id"] == model and (r["origin"], r["unit"]) in scored)
        origins = {k[0] for k in keys}
        log[model] = {
            "cases_scored": len(keys),
            "baseline_only_cases_dropped": len(set(baseline) - set(candidate)),
            "candidate_only_cases_dropped": len(set(candidate) - set(baseline)),
            "origins_scored": len(origins),
            "origins_planned": planned,
            "incomplete": len(origins) < 0.8 * planned,
        }
    (destination / "pairing_log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps(log, indent=1))


def holm(destination: Path, repetitions: int = 1000, seed: int = 20261109) -> None:
    """Holm-adjusted one-sided block-bootstrap p-values across the five indicators (registered headline).

    The bootstrap matches honestforecast.comparison: circular blocks of round(n^(1/3)) chronological origins."""
    from statistics import mean
    import random

    results = {}
    for model in INDICATORS:
        with (destination / model / "assessment" / "origin_differences.csv").open(newline="") as handle:
            values = [float(r["mean_wis_difference"]) for r in sorted(csv.DictReader(handle), key=lambda r: r["origin"])]
        n, block = len(values), max(1, round(len(values) ** (1 / 3)))
        generator, samples = random.Random(seed), []
        for _ in range(repetitions):
            drawn = []
            while len(drawn) < n:
                start = generator.randrange(n)
                drawn.extend(values[(start + k) % n] for k in range(block))
            samples.append(mean(drawn[:n]))
        results[model] = {"mean_wis_difference": mean(values), "p_one_sided": max(sum(s >= 0 for s in samples), 1) / repetitions}
    ordered = sorted(results, key=lambda m: results[m]["p_one_sided"])
    running = 0.0
    for rank, model in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * results[model]["p_one_sided"]))
        results[model]["p_holm"] = running
        results[model]["replicates_under_holm"] = results[model]["mean_wis_difference"] < 0 and running < 0.025
    (destination / "holm.json").write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=1))


def summary(output: Path) -> None:
    """Mean WIS of each model relative to AR3 and the flat line, on the cases both produced."""
    from honestforecast.metrics import weighted_interval_score

    scores = {}
    for path in sorted(output.glob("predictions_*.csv")):
        with path.open(newline="") as handle:
            scores[path.stem[len("predictions_"):]] = {
                (r["origin"], r["target_date"], r["horizon"], r["unit"]): weighted_interval_score(r) for r in csv.DictReader(handle)
            }
    for reference in ("ar3", "flatline"):
        print(f"\nmean WIS ratio vs {reference} (cases in common), by horizon:")
        for model, own in scores.items():
            if model == reference:
                continue
            cells = []
            for horizon in map(str, HORIZONS):
                keys = [k for k in own if k[2] == horizon and k in scores[reference]]
                ratio = sum(own[k] for k in keys) / sum(scores[reference][k] for k in keys) if keys else float("nan")
                cells.append(f"h{horizon}={ratio:.3f} (n={len(keys)})")
            print(f"  {model:20}", "  ".join(cells))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "check", "run", "summary", "prepare", "holm"])
    parser.add_argument("--split", choices=list(SPLITS), required=True)
    parser.add_argument("--data", choices=["asof", "finalized"], default="asof")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--assessment-dir", type=Path)
    args = parser.parse_args()
    if args.command == "fetch":
        start, end = SPLITS[args.split]
        for key in SIGNALS:
            fetch_history(*SIGNALS[key], start - timedelta(days=LOOKBACK), end)
            fetch_latest(*SIGNALS[key], start - timedelta(days=LOOKBACK), end)
        fetch_latest(*TARGET, start, end + timedelta(days=max(HORIZONS)))
        return
    if args.command == "check":
        check_snapshots()
        return
    if args.command in ("prepare", "holm"):
        destination = args.assessment_dir or Path(f"build/covid_{args.split}_{args.data}_paired")
        if args.command == "prepare":
            prepare(args.output_dir or Path(f"build/covid_{args.split}_{args.data}"), destination)
        else:
            holm(destination)
        return
    if args.command == "summary":
        summary(args.output_dir or Path(f"build/covid_{args.split}_{args.data}"))
        return
    run(args.split, args.data, args.output_dir or Path(f"build/covid_{args.split}_{args.data}"), args.workers)


if __name__ == "__main__":
    main()
