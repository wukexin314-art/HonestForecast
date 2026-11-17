# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `chng_cli`
- Candidate kind: `feature`
- Registered evidence items: `chng_cli@1`
- Protocol registration: `passed`
- Registration digest: `a5566d7f6dd7be0ab4430c467089adcdf6fe7938107cb82396e5ef578fba4be5`
- Decision state: `challenger`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 178128
- Forecast origins: 35
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 26.382400 | 17.492902 | 0.627 | 48.110 |
| Candidate | 25.094343 | 17.019098 | 0.614 | 39.254 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: -0.473804
- Mean paired MAE difference: -1.288058
- Origins improved: 0.629
- Origin-bootstrap 95% interval: [-1.123629, 0.043007]
- Drop-best-origin WIS difference: -0.018847

## Robustness warnings

- `uncertainty_includes_no_improvement`

## Audit checks

| Check | Result |
| --- | --- |
| common_grid | `passed` |
| contract_horizons | `passed` |
| feature_availability | `passed` |
| feature_manifest | `passed` |
| feature_vintage | `passed` |
| forecast_contract | `passed` |
| prediction_schema | `passed` |
| protocol_registration | `passed` |
| quantile_monotonicity | `passed` |
| structured_audit_evidence | `not_required` |

## Input hashes

- availability: `a9792e8f46dbfc002158e1ac234341df3a735f940df8ff6cf6c3d815b8a1e8ba`
- baseline: `c41a47a7ae12d816e6732ee322fcbb83200633c1c39c8d35ae1c588d1f6cbc5a`
- candidate: `6e60329a97a1989026b885e351455292b6ff32306d4e9e72e3f6b55c7aefcd42`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`
- registration: `e1bfc2133c668a65fc7f3feacaee7837eb1463f5626ea6037417558c1738199e`

## Interpretation

The candidate is promising, but the evidence is not sufficient for promotion.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
