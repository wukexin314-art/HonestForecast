# Forecast change evidence card

## Identity

- Study: `covid-auxiliary-indicators-replication-2021`
- Candidate: `chng_covid`
- Candidate kind: `feature`
- Registered evidence items: `chng_covid@1`
- Protocol registration: `not_provided`
- Registration digest: `None`
- Decision state: `challenger`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 178878
- Forecast origins: 35
- Forecast units: 306
- Horizons: 7, 14, 21
- Registered strata: trend

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 25.977340 | 17.285153 | 0.623 | 48.239 |
| Candidate | 24.397948 | 16.428183 | 0.612 | 42.434 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: -0.856969
- Mean paired MAE difference: -1.579391
- Origins improved: 0.686
- Origin-bootstrap 95% interval: [-1.941282, 0.106343]
- Drop-best-origin WIS difference: -0.347230

## Robustness warnings

- `uncertainty_includes_no_improvement`
- `material_stratum_loss:trend=falling`
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

- availability: `8ff4f3ce449d0dc6396719d498dda762b4a03e2ed262a3cbb4e6046b6791f28c`
- baseline: `78f9f3f746d54cbed261edfab05242bd88ff5354a7a7d305df15b72c5222fcfa`
- candidate: `2fc066b2915c9048dd1df18996a3a5d08b84589f6370870d5a2ef565cedddc6a`
- contract: `3b42a8369948814989797033a50f37539b993d75ffb75f5afb576c83ffdb8ab0`
- manifest: `b6e8827ef396affc77ec2123ac2049e8b3605c617c7b7a7c06a18e51abf12b41`

## Interpretation

The candidate is promising, but the evidence is not sufficient for promotion.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
