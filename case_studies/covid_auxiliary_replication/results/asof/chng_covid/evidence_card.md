# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `chng_covid`
- Candidate kind: `feature`
- Registered evidence items: `chng_covid@1`
- Protocol registration: `passed`
- Registration digest: `1d97b83d7742d938a4155e4a14c0a0079684bb42d96ea2b394d0197179edb0da`
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
| Candidate | 25.167873 | 17.035887 | 0.610 | 41.349 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: -0.457015
- Mean paired MAE difference: -1.214527
- Origins improved: 0.686
- Origin-bootstrap 95% interval: [-1.167853, 0.252615]
- Drop-best-origin WIS difference: -0.153546

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

- availability: `3ede44d4c3a98fd3e146c6d836a144c2770b611279a7a913c2d9105436638b90`
- baseline: `c41a47a7ae12d816e6732ee322fcbb83200633c1c39c8d35ae1c588d1f6cbc5a`
- candidate: `7be8566d72acfe817d504486132bb17178e9956ca35e62aec5648b707e332c18`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`
- registration: `9e612d335e677ce69bd4dcc12eee93457c7e152a8e747d87f2ccfe86c1d5ce87`

## Interpretation

The candidate is promising, but the evidence is not sufficient for promotion.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
