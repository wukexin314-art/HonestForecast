# Forecast change evidence card

## Identity

- Study: `us-ilinet-wiki-sealed-retrospective`
- Candidate: `wikipedia_influenza`
- Candidate kind: `feature`
- Registered evidence items: `wiki_influenza_en@1`
- Protocol registration: `passed`
- Registration digest: `ada9343c4f0e6397fca74ced1f764368e6897ba18fcad45f43ce42b7b99554dc`
- Decision state: `rejected`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: 1408
- Forecast origins: 64
- Forecast units: 11
- Horizons: 1, 2
- Registered strata: None

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0.547416 | 0.382594 | 0.773 | 1.367 |
| Candidate | 0.551308 | 0.384432 | 0.770 | 1.363 |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: 0.001838
- Mean paired MAE difference: 0.003892
- Origins improved: 0.484
- Origin-bootstrap 95% interval: [-0.002349, 0.006515]
- Drop-best-origin WIS difference: 0.002681

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

- availability: `10b9b2ecfd508c8bdc1a0ddc49edc25b696f0d3f6528f3bcd28894be285ec515`
- baseline: `708f785e192c7815de2dd1ba63c8545dbe1512417e92bdf31cc9bc8bcfb653d5`
- candidate: `7fe3513b3c0cc731befb123300e6cb48d4e5c94354dfa6939f64b6836bf34902`
- contract: `f5595bbae1dd6b40d5e832f3360bc604a8775c051987b9f79c27707d1fc07e74`
- manifest: `5bdfb9a7854a1a8722f6bab75adf4ccf73824770d3143def19fcf01d29f5f6ed`
- registration: `ce78b81719e0013b12928aa56ec257260dfc9601267665f8b126306e0fd3afc8`

## Interpretation

The candidate did not improve WIS under this registered representation.

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
