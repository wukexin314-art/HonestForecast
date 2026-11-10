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

`--availability` is optional for exploratory feature scoring but required when a feature or data-source candidate declares `--all-audit-gates-passed`. Promotion requires a matching protocol lock; the legacy `--confirmation-frozen` flag is not sufficient.

## Protocol registration

Run `honestforecast register --protocol protocol.json --contract forecast_contract.json --output protocol.lock.json`. The protocol freezes the study and candidate identity, confirmation window, registered strata, bootstrap repetitions, seed, and audit-check IDs. Pass the lock to assessment with `--registration`.

The lock self-hash and contract hash detect changes. Schema 1.1 locks also store `code_sha256` for `assessment.py`, `audit.py`, `comparison.py` and `metrics.py`, and `--registration` fails if any of them changed. Schema 1.0 locks still load, without the code check. Model and pipeline code is not in the lock, so pin it separately. The local timestamp is not trusted evidence that registration preceded outcome access.

Screening results report `null_pvalue`, a seeded block-permutation p-value with a floor of 0.001. It was renamed from `circular_pvalue` in 0.7.0.

For non-source candidates claiming all gates passed, supply `--audit-evidence`. Each check must match a registered ID, have status `passed`, and name an artifact plus its SHA256 digest.

The evidence JSON has `schema_version`, a candidate `{id, kind}`, and a non-empty `checks` list. Each check contains `id`, `status`, `artifact`, and `sha256`; artifact paths resolve relative to the evidence JSON.

## Candidate identity

Supported `candidate_kind` values are `feature`, `data_source`, `model`, `preprocessing`, `recalibration`, `ensemble`, and `pipeline`. Supply one stable `candidate_id` and kind in every candidate row or with `--candidate-id` and `--candidate-kind`. Legacy `feature_family` and `--family` map to a feature candidate.

## Forecast contract

Required JSON fields:

- `study_id`: stable study identifier;
- `target_name`: outcome definition;
- `frequency`: forecast frequency;
- `horizons`: unique positive integers;
- `primary_metric`: currently `WIS` for admission decisions;
- `development_only_selection`: boolean.

## Feature manifest

A manifest is required only for `feature` and `data_source` candidates. Do not invent one for model or pipeline changes.

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
- optional `unit`: non-empty series ID for a location, site, product, or population;
- `actual`, `point`: finite numbers;
- `q0.025`, `q0.1`, `q0.25`, `q0.5`, `q0.75`, `q0.9`, `q0.975`: finite, non-crossing quantiles.

Baseline and candidate `(origin, target_date, horizon, unit)` grids and actual values must match exactly.

Register subgroup columns with repeated `--stratum FIELD`. The field must be populated and identical in both prediction files for every case. A non-improving registered stratum blocks promotion when the pooled result improves.

## Availability evidence

The availability CSV contains one row for every candidate-family `feature_id` at every scored `origin` and `unit`:

- `feature_id`, `origin`, optional `unit`, `available_at`;
- optional `vintage_at`, populated on every row if used.

Keys must be unique and complete. `unit` is required when prediction files contain multiple units. `available_at` and `vintage_at` cannot be later than the forecast origin.

## Outputs

- `audit_receipt.json`: hashes, checks, claims, grid, and final decision;
- `metrics.csv`: regenerated baseline and candidate metrics;
- `origin_differences.csv`: paired origin-level differences;
- `robustness.json`: bootstrap, horizon, registered-stratum, concentration, and coverage evidence;
- `decision_log.jsonl`: append-only decision history with candidate ID and kind;
- `evidence_card.md`: human-readable summary.

Run `honestforecast verify --bundle results` to verify output hashes. Supply original input options to verify their hashes as well.
