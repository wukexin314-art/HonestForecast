# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `gs_anosmia_ageusia`
- Candidate kind: `feature`
- Registered evidence items: `gs_anosmia_ageusia@1`
- Protocol registration: `passed`
- Registration digest: `ef4f7dcffdaf0d57e58ca04b17758cc4fdcf640fad7e42e5e68127f2ee4a9d60`
- Decision state: `rejected`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 218064
- Forecast origins: 41
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 23.518720 | 15.473869 | 0.616 | 42.980 |
| Candidate | 23.391428 | 15.497055 | 0.607 | 40.340 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: 0.023187
- Mean paired MAE difference: -0.127292
- Origins improved: 0.366
- Origin-bootstrap 95% interval: [-0.173591, 0.244721]
- Drop-best-origin WIS difference: 0.143364

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

- availability: `8d4a0ec5f730ab4d4cd14d568e19c5f5be5de6fca830dd702b1fa0847d6a3460`
- baseline: `5cf20cfdec0fc16019e552839c9809df9fa11dd840d9217fbcdff165db944506`
- candidate: `6fe1768304031bc73b6f0bab194cba8013b28325a7a2c32da46743e3af923c8b`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`
- registration: `e7518d466e7ab7f297be5b638db1da08decdffa2c17e296cff14be710a49279d`

## Interpretation

The candidate did not improve WIS under this registered representation.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
