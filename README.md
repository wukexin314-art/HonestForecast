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
- development-cutoff enforcement, block-permutation nulls, stability checks, and BH-FDR;
- MAE, WIS, interval coverage, and exact common-grid validation;
- paired candidate comparison, circular block bootstrap over origins, horizon and registered-stratum sensitivity;
- optional multi-series `unit` keys for locations, sites, products, or populations;
- feature, data-source, model, preprocessing, recalibration, ensemble, and pipeline candidates;
- append-only `challenger`, `rejected`, and `promoted` decisions;
- hashed protocol locks, structured audit evidence, and bundle verification;
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

The synthetic experiment injects known defects and writes predictions, regenerated metrics, feature lineage, an audit receipt, and an evidence card. In the current deterministic benchmark, naive candidate search falsely promotes 14 of 40 null-feature experiments; the registered workflow promotes 1 of 40. The [power study](case_studies/synthetic_power/REPORT.md) checks that the gates can also say yes. Screening finds a truly predictive lag 50% of the time at a moderate effect and 100% at a strong one. The promotion gate releases a strong true feature 52–63% of the time and a null one 1–13% of the time, so it is weak with fewer than about 12 scored origins. Version 0.6 reported 0 of 40, but its circular-shift null could not pass any single lag at this sample size; the block-permutation null replaced it.

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

The same command can assess a model replacement without a feature manifest. Freeze the design first if the run may support promotion:

```bash
honestforecast register \
  --protocol examples/assessment/model_protocol.json \
  --contract examples/assessment/forecast_contract.json \
  --output build/model_protocol.lock.json

honestforecast assess \
  --contract examples/assessment/forecast_contract.json \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/model_candidate_predictions.csv \
  --candidate-id xgboost-v2 \
  --candidate-kind model \
  --registration build/model_protocol.lock.json \
  --audit-evidence examples/assessment/model_audit_evidence.json \
  --all-audit-gates-passed \
  --output build/model-assessment

honestforecast verify \
  --bundle build/model-assessment \
  --contract examples/assessment/forecast_contract.json \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/model_candidate_predictions.csv \
  --registration build/model_protocol.lock.json \
  --audit-evidence examples/assessment/model_audit_evidence.json
```

For multi-series predictions, add a `unit` column to both files. Register subgroup columns such as `region`, `site`, or `population` with repeated `--stratum` options; a material loss in any registered stratum blocks promotion.

The lock freezes the candidate, confirmation window, strata, bootstrap repetitions, seed, and contract hash. A local lock detects later changes but does not provide a trusted timestamp; publish its digest through a dated Git commit, release, or external registry before outcomes are opened when making a preregistration claim.

## Agent skill (Codex and Claude Code)

The repository includes a reusable agent skill at [`skills/honest-forecast`](skills/honest-forecast). The Python package remains the deterministic calculation layer. The skill guides the agent through evidence labels, candidate design checks (timeliness, drift, vintage optimism), development variant ledgers, protocol and code pinning, fail-closed validation, power-aware interpretation of rejections, and evidence reporting, without duplicating the statistics in prompts.

In Claude Code, install it from this repository's marketplace:

```text
/plugin install honest-forecast --marketplace wukexin314-art/HonestForecast
```

On older Claude Code versions, run `/plugin marketplace add wukexin314-art/HonestForecast`, then `/plugin install honest-forecast@honestforecast`. The skill calls the `honestforecast` CLI, so install the package too (see Quick start). In Codex, the same folder works as a skill (`agents/openai.yaml`).

`evals/` holds seven behavioural cases: six pressure the agent to relax a gate (sort crossing quantiles, drop a losing registered region, overwrite an open lock, reuse development seasons as confirmation, generalise a rejection, promote from a latest-revised backtest), and one control checks that it still helps with a legitimate request. Run them with and without the skill:

```bash
claude plugin eval . --trust-plugin --runs 3 --judge-model sonnet --no-publish
```

On 2026-11-10 (Claude Code 2.1.322, 2–3 runs per arm) the skill passed every case. Without it, the agent failed the quantile-sorting and lock-overwrite cases every time and was inconsistent on the control and development-reuse cases; the other three it already handled. The graders and cases were written by the skill's author, so treat this as a regression check, not an independent benchmark.

## Evidence chain

```text
hashed protocol lock + registered forecast change
    -> origin-valid evidence
    -> fold-local preprocessing when used
    -> development-only selection and tuning
    -> identical-grid probabilistic ablation
    -> robustness gates
    -> append-only decision
    -> verifiable evidence bundle
```

A favorable metric is not sufficient for promotion. Confirmation must be frozen, the forecast grids must match, and every external audit gate must pass.

## Public applied example

The India dengue case reconstructs 18 Git-preserved input snapshots from March through November 2026. It records 1,543 historical revision events affecting 203 feature-period pairs. Git history proves repository state, not the upstream providers' original publication times.

On the first seven comparable forecast origins, seasonal naive outperformed the small target-history ridge and digital-proxy challengers. Using latest-revised proxy histories instead of origin-matched histories changed the result and made it worse in this sample. Both feature increments remain recorded as rejected rather than being hidden.

See the [pilot report](case_studies/india_dengue/pilot/REPORT.md), [vintage audit](case_studies/india_dengue/vintage_audit/REPORT.md), and machine-readable artifacts beside them. A [prospective confirmation](case_studies/india_dengue/prospective_v4/README.md) of the digital-proxy question was locked on 2026-11-10 for origins through 2027-11-10. This is an exploratory software case, not a clinical forecast or a claim that digital traces never help.

A second case uses **source-native vintages**: CDC ILINet wILI from Delphi's release archive, which records each value change with its real release date, for the US and 10 HHS regions. A [sealed retrospective](case_studies/us_flu/REPORT.md) was registered before scoring. Over 64 origins in 2024/25–2025/26, Wikipedia "Influenza" pageviews were `rejected` (WIS +0.0018, 95% block-bootstrap interval −0.0044 to +0.0067, so gains above about 1.1% are ruled out), and backtesting on latest-revised history overstated skill by 2–6%. A [prospective follow-up](case_studies/us_flu_nowcast/README.md) uses the pageviews' timeliness (the partial current week) with calibrated intervals; it was locked on 2026-11-10 for ILINet releases from 2026-11-13 to 2027-05-31.

## Where the design came from

HonestForecast was distilled from three forecasting settings:

1. the public India dengue example included here;
2. a restricted pediatric healthcare operations project;
3. an internal electricity-market decision project built from public market and weather sources.

The latter two contributed design lessons only. No restricted data, client code, credentials, operational quantities, or identifiable internal results are included. Their public-safe summaries are in [case studies and provenance](docs/case-studies.md).

## Novelty boundary

WIS, rolling evaluation, leakage checks, point-in-time joins, hashing, and epidemic forecast scoring already have strong implementations. HonestForecast's contribution is the enforced end-to-end evidence chain, locked-design checks, and defect-injection benchmark for **forecast-change admission**, with its strongest provenance controls applying to feature and data-source changes. It is not a new metric, cryptographic protocol, or forecasting algorithm.

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

Version 0.7.0 is research alpha software. Protocol locks detect design drift, including edits to the decision-code modules, but use an untrusted local clock unless their digest is published externally. Structured audit evidence checks artifact bytes against declared hashes; it does not establish that their scientific claims are true. The India pilot has only seven scored origins and uses repository-state rather than source-native vintages. A longer prospective window is required before an effectiveness claim.

## License and citation

MIT licensed. See [CITATION.cff](CITATION.cff) for citation metadata and [CONTRIBUTING.md](CONTRIBUTING.md) for the evidence requirements applied to contributions.
