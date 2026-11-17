# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `dv_cli`
- Candidate kind: `feature`
- Registered evidence items: `dv_cli@1`
- Protocol registration: `passed`
- Registration digest: `4f3e36f070e5bfdd33a1840a965cf9c9b3f50e1f20b38ce34d234c3aebc0ed91`
- Decision state: `rejected`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 217998
- Forecast origins: 41
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 23.522237 | 15.476451 | 0.616 | 42.984 |
| Candidate | 22.887535 | 15.661050 | 0.600 | 36.965 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: 0.184599
- Mean paired MAE difference: -0.634702
- Origins improved: 0.415
- Origin-bootstrap 95% interval: [-0.594219, 1.055940]
- Drop-best-origin WIS difference: 0.509317

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
| protocol_registration | `passed` |
| quantile_monotonicity | `passed` |
| structured_audit_evidence | `not_required` |

## Input hashes

- availability: `f62f0cd1f16f6a4c648a4e03435ea0fc8c13db0f0399ddb024e0f9ce9f19a0fe`
- baseline: `0732e5f215196157846c2927ab8e9ba9ba66fe5f85930891ab1ee1bb8b79631b`
- candidate: `7e9228e93cd14ae4bbbb7cee392c927ace90c1bfe9c0a95d582d54a8df469844`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`
- registration: `9475425efcb4bb2d2aebe01653a71dcc0aed5983018456f55805c03ace2ccff4`

## Interpretation

The candidate did not improve WIS under this registered representation.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
