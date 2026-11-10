# Promotion interpretation

Read this reference before interpreting a decision or recommending feature admission.

## Difference direction

HonestForecast reports candidate minus baseline differences. Negative WIS or MAE differences favor the candidate. Coverage difference is candidate minus baseline, so a negative value is degradation.

## Decision states

- `promoted`: the candidate improves paired WIS, passes registered robustness rules, and the run declares both frozen confirmation and all audit gates passed with availability evidence.
- `challenger`: the paired WIS point estimate favors the candidate, but robustness, audit, or confirmation evidence is incomplete.
- `rejected`: paired mean WIS does not favor the candidate under the tested representation.
- Invalid schemas, unequal grids, mismatched actuals, unavailable-at-origin features, or crossing quantiles stop the assessment rather than producing a ranked state.

## Registered robustness warnings

- `event_concentration`: removing the best origin removes or reverses the gain;
- `coverage_degradation`: registered interval coverage falls by more than five percentage points;
- `fewer_than_60_percent_origins_improved`;
- `uncertainty_includes_no_improvement`: the origin-bootstrap upper bound is at least zero;
- `material_horizon_loss`: pooled improvement hides a non-improving registered horizon.
- `material_stratum_loss:<field>=<value>`: pooled improvement hides a non-improving registered subgroup.

Any registered warning prevents promotion. Do not discard a warning because a different metric or unregistered subgroup looks favorable.

## Claim boundary

The software verifies consistency of supplied artifacts. It does not independently verify that source timestamps, version labels, confirmation declarations, or audit attestations are true. State that condition when reporting `promoted`. A predictive improvement is not evidence of causality, clinical validity, or safe deployment.
