# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `ctis_cmnty_cli`
- Candidate kind: `feature`
- Registered evidence items: `ctis_cmnty_cli@1`
- Protocol registration: `passed`
- Registration digest: `ff677681334379b4477afb7dc559cdfe458f8ca7e2023581d3fe338756a1ba41`
- Decision state: `rejected`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 215100
- Forecast origins: 41
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 23.266833 | 15.301875 | 0.617 | 42.654 |
| Candidate | 22.830668 | 15.399069 | 0.610 | 35.509 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: 0.097194
- Mean paired MAE difference: -0.436165
- Origins improved: 0.756
- Origin-bootstrap 95% interval: [-0.369613, 0.726502]
- Drop-best-origin WIS difference: 0.139450

## Robustness warnings

- `event_concentration`
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

- availability: `5a704a7a393559038806a5158d7ce3acec5580fffab1ac783db154b9c760ef75`
- baseline: `4cd33742c5f1dac8547ea431f61a437add09bb04a71a486d817a509260073688`
- candidate: `a70e2fe95fad49a161ac297ca77d840fcc63ae5d499d0a2b6bc257a56e3b73d0`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`
- registration: `ae9ccb8623caef199f0e9e46ff70608aa99ba7cbba0d8fdb6723362721609856`

## Interpretation

The candidate did not improve WIS under this registered representation.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
