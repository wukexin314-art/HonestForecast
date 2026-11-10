# Portable feature assessment

`honestforecast assess` compares one candidate feature family with one baseline. The predictions may come from skforecast, scikit-learn, R, a spreadsheet, or a custom model. HonestForecast does not refit those models.

## Run the bundled example

```bash
honestforecast assess \
  --contract examples/assessment/forecast_contract.json \
  --manifest examples/assessment/feature_manifest.csv \
  --baseline examples/assessment/baseline_predictions.csv \
  --candidate examples/assessment/candidate_predictions.csv \
  --availability examples/assessment/availability.csv \
  --output build/assessment
```

The example remains a `challenger` because it is not presented as frozen confirmation evidence.

## Prediction schema

Baseline and candidate files require one row per forecast case and these columns:

| Column | Meaning |
| --- | --- |
| `origin` | ISO date when the forecast was issued |
| `target_date` | ISO date of the predicted outcome |
| `horizon` | Positive integer matching the forecast contract |
| `actual` | Mature observed outcome |
| `point` | Point forecast |
| `q0.025` ... `q0.975` | Seven registered, non-crossing forecast quantiles |

The candidate must also contain a single `feature_family` value, unless the same value is supplied with `--family`. Baseline and candidate keys and actual values must match exactly.

## Availability evidence

`--availability` accepts one row per candidate `feature_id` and forecast `origin`:

| Column | Meaning |
| --- | --- |
| `feature_id` | ID registered in the candidate family manifest |
| `origin` | Forecast origin |
| `available_at` | Date on which the used value was available |
| `vintage_at` | Optional snapshot date; if present, it is required on every row |

Missing pairs, duplicate pairs, values available after the origin, and future snapshots fail the assessment. Scoring without this file is allowed, but `--all-audit-gates-passed` is not.

## Outputs

- `audit_receipt.json`: contract, hashes, checks, grid, claims, and decision;
- `metrics.csv`: regenerated baseline and candidate metrics;
- `origin_differences.csv`: paired origin-level WIS and MAE differences;
- `robustness.json`: decision details and horizon sensitivity;
- `decision_log.jsonl`: append-only feature-family outcomes;
- `evidence_card.md`: a reviewable summary generated from the saved evidence.

Differences are candidate minus baseline, so negative WIS and MAE differences favor the candidate.

## Promotion claims

The default result can be `challenger` or `rejected`. A `promoted` result additionally requires both `--confirmation-frozen` and `--all-audit-gates-passed`, plus origin-level availability evidence. These flags are explicit study declarations, not facts independently discovered by the software. The evidence card keeps that limitation visible.
