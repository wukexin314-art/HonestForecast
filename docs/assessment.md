# Portable forecast-change assessment

`honestforecast assess` compares one registered forecast change with one baseline. Predictions may come from skforecast, scikit-learn, R, a spreadsheet, or a custom model. HonestForecast scores and audits supplied predictions; it does not refit the models.

## Candidate types

`candidate_kind` accepts:

- `feature` and `data_source`, which require a feature manifest and support origin-level availability evidence;
- `model`, `preprocessing`, `recalibration`, `ensemble`, and `pipeline`, which use explicit study attestations for provenance gates not visible in prediction files.

Every candidate has one stable `candidate_id`. Existing `feature_family` inputs and `--family` remain supported as the legacy feature-candidate interface.

## Run the feature example

```bash
honestforecast assess \
  --contract examples/assessment/forecast_contract.json \
  --manifest examples/assessment/feature_manifest.csv \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/candidate_predictions.csv \
  --availability examples/assessment/availability.csv \
  --output build/assessment
```

## Run the model example

```bash
honestforecast assess \
  --contract examples/assessment/forecast_contract.json \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/model_candidate_predictions.csv \
  --candidate-id xgboost-v2 \
  --candidate-kind model \
  --output build/model-assessment
```

Both examples remain `challenger` because they are not presented as frozen confirmation evidence.

## Prediction schema

Baseline and candidate files require one row per forecast case and these columns:

| Column | Meaning |
| --- | --- |
| `origin` | ISO date when the forecast was issued |
| `target_date` | ISO date of the predicted outcome |
| `horizon` | Positive integer matching the forecast contract |
| `unit` | Optional series ID for a location, site, product, or population |
| `actual` | Mature observed outcome |
| `point` | Point forecast |
| `q0.025` ... `q0.975` | Seven registered, non-crossing forecast quantiles |

The candidate additionally declares one `candidate_id` and `candidate_kind` on every row, or receives them through command options. Feature candidates may continue using `feature_family`. Baseline and candidate `(origin, target_date, horizon, unit)` keys and actual values must match exactly.

## Registered strata

Add the same subgroup column to both prediction files and register it explicitly:

```bash
honestforecast assess ... --stratum region --stratum population
```

The output reports WIS differences for every registered value. If the pooled candidate improves but any registered stratum does not, `material_stratum_loss:<field>=<value>` blocks promotion. Strata are not discovered post hoc.

## Availability evidence

Feature and data-source candidates may use `--availability`. It accepts one row for every candidate `feature_id`, forecast `origin`, and optional `unit`:

| Column | Meaning |
| --- | --- |
| `feature_id` | ID registered in the candidate family manifest |
| `origin` | Forecast origin |
| `unit` | Required when prediction files contain multiple units |
| `available_at` | Date on which the used value was available |
| `vintage_at` | Optional snapshot date; if present, required on every row |

Missing or duplicate pairs, values available after the origin, and future snapshots fail the assessment. A feature or data-source candidate can be scored without this file, but it cannot declare all audit gates passed.

## Outputs

- `audit_receipt.json`: contract, candidate identity, hashes, checks, grid, claims, and decision;
- `metrics.csv`: regenerated baseline and candidate metrics;
- `origin_differences.csv`: paired origin-level WIS and MAE differences;
- `robustness.json`: horizon and registered-stratum sensitivity;
- `decision_log.jsonl`: append-only outcomes with candidate ID and kind;
- `evidence_card.md`: a reviewable summary generated from saved evidence.

Differences are candidate minus baseline, so negative WIS and MAE differences favor the candidate.

## Promotion claims

The default result can be `challenger` or `rejected`. A `promoted` result additionally requires both `--confirmation-frozen` and `--all-audit-gates-passed`, plus origin-level availability evidence for feature and data-source candidates. These flags are study declarations, not facts independently discovered by the software. A registered horizon or stratum warning prevents promotion.
