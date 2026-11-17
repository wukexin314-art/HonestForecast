# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `dv_cli`
- Candidate kind: `feature`
- Registered evidence items: `dv_cli@1`
- Protocol registration: `not_provided`
- Registration digest: `None`
- Decision state: `rejected`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 218889
- Forecast origins: 41
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 23.142375 | 15.276967 | 0.613 | 43.012 |
| Candidate | 22.257372 | 15.309928 | 0.601 | 36.534 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: 0.032962
- Mean paired MAE difference: -0.885002
- Origins improved: 0.488
- Origin-bootstrap 95% interval: [-0.890013, 0.996062]
- Drop-best-origin WIS difference: 0.465262

## Robustness warnings

- `event_concentration`
- `fewer_than_60_percent_origins_improved`
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
| protocol_registration | `not_provided` |
| quantile_monotonicity | `passed` |
| structured_audit_evidence | `not_required` |

## Input hashes

- availability: `80414ca5de40c5ad164f0d4eb8ead86533eb212724c2181156a09a75ca58ac37`
- baseline: `ccb9a1db25ae55f62db496207ae4595a113a2398f2d52e0ee5ed331afa62c950`
- candidate: `458068425af6b8dcab79fe4ea48502e72b038ea1f31c058b83c170b208eeea02`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`

## Interpretation

The candidate did not improve WIS under this registered representation.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
