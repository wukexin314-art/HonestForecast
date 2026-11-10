# HonestForecast

**Evidence-first feature engineering for forecasts built from delayed, revised, or operationally fragile data.**

HonestForecast is a small Python toolkit for answering a question that ordinary backtests often skip:

> Did a feature improve the forecast using only the information that was actually available at each forecast origin?

It connects point-in-time feature provenance, fold-local preprocessing, development-only screening, common-grid probabilistic ablation, robustness gates, and append-only decisions. The package is intentionally not a model zoo.

## Why this exists

A feature can look useful retrospectively and still be invalid or unsafe to deploy because:

- the value was published after the forecast origin;
- a later revision was used as if it were the original value;
- preprocessing was fitted on future rows;
- many candidates were searched and only the winner was reported;
- a gain came from one event, one horizon, or worse interval coverage;
- predictive signal did not translate into the decision the forecast supports.

HonestForecast makes those failure modes explicit and testable.

## What is included

- forecast and feature contracts;
- origin-aware as-of joins for revised features;
- registered lag, trailing-mean, momentum, log, and Fourier transforms;
- fold-local imputation and clipping with lineage;
- development-cutoff enforcement, circular-shift nulls, stability checks, and BH-FDR;
- MAE, WIS, interval coverage, and exact common-grid validation;
- paired feature-family ablation, origin bootstrap, horizon and event sensitivity;
- append-only `challenger`, `rejected`, and `promoted` decisions;
- deterministic synthetic leakage and false-promotion scenarios;
- Git-history data-vintage auditing;
- a public India dengue repository-vintage pilot.

## Quick start

HonestForecast has no runtime dependencies outside the Python standard library.

```bash
git clone https://github.com/wukexin314-art/HonestForecast.git
cd HonestForecast
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
honestforecast-synthetic --output-dir build/synthetic
```

The synthetic experiment injects known defects and writes predictions, regenerated metrics, feature lineage, an audit receipt, and an evidence card. In the current deterministic benchmark, naive candidate search falsely promotes 17 of 40 null-feature experiments; the registered workflow promotes 0 of 40.

## Evidence chain

```text
feature mechanism + manifest
    -> origin-available vintage
    -> fold-local transformation
    -> development-only screening
    -> identical-grid probabilistic ablation
    -> robustness gates
    -> append-only decision
    -> evidence card
```

A favorable metric is not sufficient for promotion. Confirmation must be frozen, the forecast grids must match, and every external audit gate must pass.

## Public applied example

The India dengue case reconstructs 18 Git-preserved input snapshots from March through November 2026. It records 1,543 historical revision events affecting 203 feature-period pairs. Git history proves repository state, not the upstream providers' original publication times.

On the first seven comparable forecast origins, seasonal naive outperformed the small target-history ridge and digital-proxy challengers. Using latest-revised proxy histories instead of origin-matched histories changed the result and made it worse in this sample. Both feature increments remain recorded as rejected rather than being hidden.

See the [pilot report](case_studies/india_dengue/pilot/REPORT.md), [vintage audit](case_studies/india_dengue/vintage_audit/REPORT.md), and machine-readable artifacts beside them. This is an exploratory software case, not a clinical forecast or a claim that digital traces never help.

## Where the design came from

HonestForecast was distilled from three forecasting settings:

1. the public India dengue example included here;
2. a restricted pediatric healthcare operations project;
3. an internal electricity-market decision project built from public market and weather sources.

The latter two contributed design lessons only. No restricted data, client code, credentials, operational quantities, or identifiable internal results are included. Their public-safe summaries are in [case studies and provenance](docs/case-studies.md).

## Novelty boundary

WIS, rolling evaluation, leakage checks, point-in-time joins, and epidemic forecast scoring already have strong implementations. HonestForecast's contribution is the enforced end-to-end evidence chain and defect-injection benchmark for **feature-family admission**, not a new metric or forecasting algorithm.

See the [landscape review](docs/landscape.md) for the nearest projects, overlaps, and claims this project deliberately does not make.

## Repository map

```text
src/honestforecast/               core package and three CLIs
tests/                            unit and committed-artifact checks
examples/                         forecast contract and feature manifest
case_studies/india_dengue/        public reports and machine-readable evidence
docs/                             protocol, feature engineering, landscape, provenance
scripts/public_safety_scan.py     private-artifact guard
```

## Status

Version 0.3.0 is research alpha software. The India pilot has only seven scored origins and uses repository-state rather than source-native vintages. A longer prospective window is required before an effectiveness claim.

## License and citation

MIT licensed. See [CITATION.cff](CITATION.cff) for citation metadata and [CONTRIBUTING.md](CONTRIBUTING.md) for the evidence requirements applied to contributions.
