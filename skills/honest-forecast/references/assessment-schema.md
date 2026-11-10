# Assessment input and output schema

Read this reference when creating, validating, or repairing artifacts for `honestforecast assess`.

## Command

```bash
honestforecast assess \
  --contract forecast_contract.json \
  --manifest feature_manifest.csv \
  --baseline baseline_predictions.csv \
  --candidate candidate_predictions.csv \
  --availability availability.csv \
  --output results
```

`--availability` is optional for exploratory scoring but required with `--all-audit-gates-passed`. A promotion additionally requires `--confirmation-frozen`. `--family NAME` may replace the candidate `feature_family` column.

## Forecast contract

Required JSON fields:

- `study_id`: stable study identifier;
- `target_name`: outcome definition;
- `frequency`: forecast frequency;
- `horizons`: unique positive integers;
- `primary_metric`: currently `WIS` for admission decisions;
- `development_only_selection`: boolean.

## Feature manifest

Required CSV columns:

- `feature_id`, `family`, `version`;
- `availability_class`: `known_ahead`, `observed_with_lag`, `forecast_required`, or `unverified`;
- `minimum_reporting_lag`, `vintage_policy`;
- `state`: a registered feature state such as `candidate`, `challenger`, or `rejected`.

Every candidate family feature must have a unique `(feature_id, version)` pair. An `unverified` feature cannot support all audit gates passing.

## Prediction files

Both prediction CSVs require one row per case and these columns:

- `origin`, `target_date`: ISO dates;
- `horizon`: positive integer registered in the contract;
- `actual`, `point`: finite numbers;
- `q0.025`, `q0.1`, `q0.25`, `q0.5`, `q0.75`, `q0.9`, `q0.975`: finite, non-crossing quantiles.

The candidate also declares one `feature_family` value on every row unless `--family` is supplied. Baseline and candidate grids and actual values must match exactly.

## Availability evidence

The availability CSV contains one row for every candidate-family `feature_id` at every scored `origin`:

- `feature_id`, `origin`, `available_at`;
- optional `vintage_at`, populated on every row if used.

Pairs must be unique and complete. `available_at` and `vintage_at` cannot be later than the forecast origin.

## Outputs

- `audit_receipt.json`: hashes, checks, claims, grid, and final decision;
- `metrics.csv`: regenerated baseline and candidate metrics;
- `origin_differences.csv`: paired origin-level differences;
- `robustness.json`: bootstrap, horizon, concentration, and coverage evidence;
- `decision_log.jsonl`: append-only decision history;
- `evidence_card.md`: human-readable summary.
