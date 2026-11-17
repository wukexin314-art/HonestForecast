# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `ctis_cmnty_cli`
- Candidate kind: `feature`
- Registered evidence items: `ctis_cmnty_cli@1`
- Protocol registration: `not_provided`
- Registration digest: `None`
- Decision state: `rejected`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 215994
- Forecast origins: 41
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 22.894309 | 15.102479 | 0.615 | 42.700 |
| Candidate | 22.575806 | 15.277136 | 0.603 | 34.925 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: 0.174658
- Mean paired MAE difference: -0.318503
- Origins improved: 0.732
- Origin-bootstrap 95% interval: [-0.329882, 0.886801]
- Drop-best-origin WIS difference: 0.206493

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
| protocol_registration | `not_provided` |
| quantile_monotonicity | `passed` |
| structured_audit_evidence | `not_required` |

## Input hashes

- availability: `5dccab434a5c21431ec772e056cdb772118574ecba5d4e3447b67837febd682d`
- baseline: `43a651f415e690c7d5946f1d36075057e4c30503bc0ee25074551bbf87ccf845`
- candidate: `5f4e651e98a819c708236b66d8f065f5586a457e5d7ad4e572327ee893056eb1`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`

## Interpretation

The candidate did not improve WIS under this registered representation.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
