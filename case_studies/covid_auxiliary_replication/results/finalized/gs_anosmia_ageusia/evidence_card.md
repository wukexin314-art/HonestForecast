# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `gs_anosmia_ageusia`
- Candidate kind: `feature`
- Registered evidence items: `gs_anosmia_ageusia@1`
- Protocol registration: `not_provided`
- Registration digest: `None`
- Decision state: `challenger`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 218955
- Forecast origins: 41
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 23.138834 | 15.274374 | 0.613 | 43.007 |
| Candidate | 22.990160 | 15.231017 | 0.606 | 40.271 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: -0.043356
- Mean paired MAE difference: -0.148673
- Origins improved: 0.439
- Origin-bootstrap 95% interval: [-0.296390, 0.201164]
- Drop-best-origin WIS difference: 0.124736

## Robustness warnings

- `event_concentration`
- `fewer_than_60_percent_origins_improved`
- `uncertainty_includes_no_improvement`
- `material_stratum_loss:trend=flat`
- `registration_missing`
- `audit_gates_unconfirmed`

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

- availability: `020843019f5a04e17b400dade322e20ad9b61c29c15e3459bc0dab99fac5706f`
- baseline: `3a16b47de8edc67707bd73424efcc8b56aaa08945f1c85ddc064b8eca8fb602f`
- candidate: `323e04fcd16ca1e52f06adc308f89e0969cfc9cb648c50b55302a66a54c57ff5`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`

## Interpretation

The candidate is promising, but the evidence is not sufficient for promotion.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
