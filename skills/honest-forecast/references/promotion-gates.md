# Promotion interpretation

Read this reference before interpreting a decision or recommending feature admission.

## Difference direction

HonestForecast reports candidate minus baseline differences. Negative WIS or MAE differences favor the candidate. Coverage difference is candidate minus baseline, so a negative value is degradation.

## Decision states

- `promoted`: the candidate improves paired WIS, passes registered robustness rules, matches a protocol lock, and declares all audit gates passed with the required availability or structured audit evidence.
- `challenger`: the paired WIS point estimate favors the candidate, but robustness, audit, or confirmation evidence is incomplete.
- `rejected`: paired mean WIS does not favor the candidate under the tested representation.
- Invalid schemas, unequal grids, mismatched actuals, unavailable-at-origin features, or crossing quantiles stop the assessment rather than producing a ranked state.

## Registered robustness warnings

- `event_concentration`: removing the best origin removes or reverses the gain;
- `coverage_degradation`: registered interval coverage falls by more than five percentage points;
- `fewer_than_60_percent_origins_improved`;
- `uncertainty_includes_no_improvement`: the upper bound of the origin block bootstrap (circular, block length round(n^(1/3)) over chronological origins) is at least zero;
- `material_horizon_loss`: pooled improvement hides a non-improving registered horizon.
- `material_stratum_loss:<field>=<value>`: pooled improvement hides a non-improving registered subgroup.
- `registration_missing`: the assessment lacks a matching locked protocol.
- `audit_gates_unconfirmed`: the required audit evidence or declaration is incomplete.

Any registered warning prevents promotion. Do not discard a warning because a different metric or unregistered subgroup looks favorable.

## Reading a rejection: power

A gate can only say no if it can also say yes. From the repository's synthetic power study (`case_studies/synthetic_power/REPORT.md`, two horizons):

| Scored origins | Null feature released | Strong true feature released |
| ---: | ---: | ---: |
| 6 | 13% | 43% |
| 12 | 5% | 45% |
| 24 | 2% | 50% |
| 36 | 1% | 56% |

- Below about 12 origins, a `rejected` or `challenger` result is weak evidence in either direction. Say so.
- With enough origins, quote what the result rules out: `-bootstrap_95_lower / baseline WIS`. Example: lower bound −0.0044 on a baseline WIS of 0.3826 rules out average gains above about 1.1%. Bundles from before the block bootstrap (any lock whose `comparison.py` hash is `385476ab…`) used an iid origin resample, which is too narrow for autocorrelated origins; say so when quoting them.
- `coverage_degradation` uses a fixed 5-point threshold, so with few cases one extra miss can trigger it. Report it, but note when it is the only warning.
- A design defect is not a null result. If the candidate did not use its availability advantage, or entered a drifting source as a raw level, describe the rejection as applying to that representation only.

## Vintage optimism

When the source keeps release history, compare each model trained and scored on as-of history with the same model on latest-revised history. Report the WIS gap: negative means the retrospective backtest looks better than real time. If the gap differs between baseline and candidate, it can change which one wins. In the bundled cases it was 2–6% for ILINet (same for both models), and it reversed the ordering in the Git-state dengue pilot.

## Claim boundary

The software verifies consistency and hashes of supplied artifacts. It does not independently verify that source timestamps, version labels, or scientific assertions inside audit artifacts are true. A local registration timestamp is not trusted chronology. State those conditions when reporting `promoted`. A predictive improvement is not evidence of causality, clinical validity, or safe deployment.
