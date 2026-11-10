# Synthetic power study: does the gate release real improvements?

A false-promotion rate of zero means little unless a truly useful change can still pass. This study injects a feature with a known effect and measures how often each rule releases it.

Regenerate: `honestforecast-synthetic --output-dir build/synthetic --power-repetitions 500` (screening uses the same count; the committed screening table used 200).

## Design

- Target: `y_t = 10 + 2 sin(2πt/12) + u_t + β x_{t-2}`, with AR(1) noise `u` (φ = 0.5) and an AR(1) feature `x` (φ = 0.6, unit variance).
- `effect` = signal sd of `β x` divided by the noise sd of `u`. `effect = 0` is a null feature.
- Baseline: direct h-step ridge on season plus the last target value. Candidate: the same model plus `x_{t+h-2}`, which is available at the origin. The models are refit at every origin on an expanding window (48 burn-in months), with Gaussian intervals from the residual spread. Horizons 1 and 2.
- **Naive rule:** release if the mean paired WIS improves. **Gate:** `compare_candidate` gives `challenger` with no registered warning, which is what `assess` needs for `promoted` once the lock and audit gates pass.
- 500 replicates per cell. The first *n* origins of each replicate are scored, so smaller windows are prefixes of larger ones.

## Promotion gate (`gate_power.csv`)

Release rate (naive / gate):

| effect \ scored origins | 6 | 12 | 24 | 36 |
| --- | --- | --- | --- | --- |
| 0 (null) | 0.38 / **0.13** | 0.31 / **0.05** | 0.25 / **0.02** | 0.21 / **0.01** |
| 0.25 | 0.55 / 0.21 | 0.55 / 0.13 | 0.52 / 0.10 | 0.56 / 0.09 |
| 0.5 | 0.72 / 0.35 | 0.74 / 0.26 | 0.80 / 0.25 | 0.86 / 0.25 |
| 1.0 | 0.85 / 0.52 | 0.89 / 0.50 | 0.96 / 0.57 | 0.98 / 0.63 |

Findings:

1. The gate does release real signal: a strong feature passes 52–63% of the time, versus 1–13% for a null feature.
2. With 6 scored origins the gate is weak in both directions. A null feature passes 13% of the time, and a strong one passes about half the time (52%).
3. The binding rule is now the interval itself: `uncertainty_includes_no_improvement` fires in 33–49% of strong-feature runs, then the 60%-of-origins rule (7–24%). Power for small and medium effects still hardly grows with more origins. See the `warning_rate:*` columns.

**Rule history.** Two changes on 2026-11-10 moved these numbers, and the null row barely moved in either:

| Decision code | Strong feature released | Null released | Strong runs vetoed by `coverage_degradation` |
| --- | ---: | ---: | ---: |
| iid origin bootstrap, fixed 5-point coverage veto, any non-improving horizon vetoes | 45–63% | 1–13% | 28–43% |
| + circular block bootstrap (block round(n^(1/3))) | 43–56% | 1–13% | 28–43% |
| + coverage veto needs a block-bootstrap interval below zero; horizon/stratum veto needs a loss distinguishable from the pooled gain | 52–63% | 1–13% | 6–8% |

The fixed 5-point coverage veto was the main source of lost power: one or two extra misses in a few dozen cases could block a real improvement that WIS, which already scores calibration, rewarded.

## Screening stage (`screening_power.csv`)

Same 12-lag search as the original null experiment, with lag 2 made truly predictive (200 replicates). Current method, a block-permutation null:

| effect | naive "any lag p ≤ 0.05" | honest: any lag eligible | honest: true lag eligible |
| --- | ---: | ---: | ---: |
| 0 | 0.41 | 0.035 | 0.005 |
| 0.25 | 0.59 | 0.11 | 0.095 |
| 0.5 | 0.87 | 0.51 | 0.50 |
| 1.0 | 1.00 | 1.00 | 1.00 |

The false-release rate under the null is 3.5%, close to the 5% BH target, and a true lag is now found once its effect is moderate.

**Fixed defect (v0.6 circular-shift null).** Before this change, honest screening released nothing at any effect size, 0.00 in every row. The circular-shift p-value is at least `1/n` (n − 1 shifts). With n = 46 the floor is 0.0217. Benjamini–Hochberg across 12 candidates then requires the smallest p-value to be at most 0.05/12 ≈ 0.0042. Even a perfectly correlated feature got an adjusted p of 0.26. So the old "0 of 40" result was guaranteed by that floor.

`screening.block_permutation_pvalue` fixes this. It rotates the target at a random offset, shuffles blocks of about √n to keep short-range autocorrelation, and takes 999 seeded draws, so the floor is 0.001. The result field is renamed `circular_pvalue` → `null_pvalue`.

## Limits

- One data-generating process, Gaussian noise, and a linear true effect. Real outbreaks are heavier-tailed.
- Monte Carlo standard error per gate cell is about 0.02 (500 replicates).
- The confirmation-window and audit-evidence gates are assumed to pass. This study measures only the statistical rules.
