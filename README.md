# HonestForecast

**Evidence gates for forecast changes under delayed, revised, or drifting data.**

HonestForecast is a small Python toolkit for answering a question that ordinary backtests often skip:

> Did a registered feature, model, data source, or pipeline change improve the forecast on evidence that was genuinely available at each origin?

It connects point-in-time provenance, fold-local preprocessing, development-only screening, common-grid probabilistic comparison, subgroup robustness gates, and append-only decisions. The package is intentionally not a model zoo.

## Why this exists

A forecast change can look useful retrospectively and still be invalid or unsafe to deploy because:

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
- paired candidate comparison, origin bootstrap, horizon and registered-stratum sensitivity;
- optional multi-series `unit` keys for locations, sites, products, or populations;
- feature, data-source, model, preprocessing, recalibration, ensemble, and pipeline candidates;
- append-only `challenger`, `rejected`, and `promoted` decisions;
- deterministic synthetic leakage and false-promotion scenarios;
- Git-history data-vintage auditing;
- a public India dengue repository-vintage pilot.

## Quick start

HonestForecast has no runtime dependencies outside the Python standard library.

```bash
git clone https://github.com/wukexin314-art/HonestForecast.git
cd HonestForecast
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
honestforecast-synthetic --output-dir build/synthetic
```

The synthetic experiment injects known defects and writes predictions, regenerated metrics, feature lineage, an audit receipt, and an evidence card. In the current deterministic benchmark, naive candidate search falsely promotes 17 of 40 null-feature experiments; the registered workflow promotes 0 of 40.

## Assess predictions from any model

HonestForecast can audit paired probabilistic predictions produced by skforecast, scikit-learn, R, a spreadsheet, or a custom model:

```bash
honestforecast assess \
  --contract examples/assessment/forecast_contract.json \
  --manifest examples/assessment/feature_manifest.csv \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/candidate_predictions.csv \
  --availability examples/assessment/availability.csv \
  --output build/assessment
```

The command requires an exact evaluation grid, validates forecast quantiles and origin-level feature availability, runs paired robustness checks, appends the decision, and emits an evidence card. See the [portable assessment guide](docs/assessment.md) for schemas and interpretation.

The same command can assess a model replacement without a feature manifest:

```bash
honestforecast assess \
  --contract examples/assessment/forecast_contract.json \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/model_candidate_predictions.csv \
  --candidate-id xgboost-v2 \
  --candidate-kind model \
  --output build/model-assessment
```

For multi-series predictions, add a `unit` column to both files. Register subgroup columns such as `region`, `site`, or `population` with repeated `--stratum` options; a material loss in any registered stratum blocks promotion.

## Codex Skill

The repository includes a reusable Codex Skill at [`skills/honest-forecast`](skills/honest-forecast). The Python package remains the deterministic calculation layer; the Skill guides Codex through contracts, availability evidence, fail-closed validation, promotion interpretation, and evidence reporting without duplicating the statistics in prompts.

## Evidence chain

```text
registered forecast change + applicable provenance
    -> origin-valid evidence
    -> fold-local preprocessing when used
    -> development-only selection and tuning
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

WIS, rolling evaluation, leakage checks, point-in-time joins, and epidemic forecast scoring already have strong implementations. HonestForecast's contribution is the enforced end-to-end evidence chain and defect-injection benchmark for **forecast-change admission**, with its strongest provenance controls applying to feature and data-source changes. It is not a new metric or forecasting algorithm.

See the [landscape review](docs/landscape.md) for the nearest projects, overlaps, and claims this project deliberately does not make.

## Repository map

```text
src/honestforecast/               core package and command-line entry points
tests/                            unit and committed-artifact checks
examples/                         contracts, manifests, and portable assessment inputs
case_studies/india_dengue/        public reports and machine-readable evidence
docs/                             protocol, feature engineering, landscape, provenance
scripts/public_safety_scan.py     private-artifact guard
skills/honest-forecast/           reusable Codex workflow and references
```

## Status

Version 0.5.0 is research alpha software. Generic model and pipeline decisions rely on explicit researcher attestations for gates the supplied prediction files cannot independently verify. The India pilot has only seven scored origins and uses repository-state rather than source-native vintages. A longer prospective window is required before an effectiveness claim.

## License and citation

MIT licensed. See [CITATION.cff](CITATION.cff) for citation metadata and [CONTRIBUTING.md](CONTRIBUTING.md) for the evidence requirements applied to contributions.
