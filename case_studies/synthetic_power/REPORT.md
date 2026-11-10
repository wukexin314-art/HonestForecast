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
| 0 (null) | 0.38 / **0.13** | 0.31 / **0.04** | 0.25 / **0.03** | 0.21 / **0.01** |
| 0.25 | 0.55 / 0.19 | 0.55 / 0.14 | 0.52 / 0.13 | 0.56 / 0.12 |
| 0.5 | 0.72 / 0.32 | 0.74 / 0.26 | 0.80 / 0.30 | 0.86 / 0.32 |
| 1.0 | 0.85 / 0.45 | 0.89 / 0.48 | 0.96 / 0.57 | 0.98 / 0.63 |

Findings:

1. The gate does release real signal: a strong feature passes 45–63% of the time, versus 1–13% for a null feature.
2. With 6 scored origins the gate is weak in both directions. A null feature passes 13% of the time, and a strong one passes less than half the time. Short confirmation windows cannot settle a feature question.
3. For small and medium effects, power hardly grows with more origins. The `coverage_degradation` rule binds at a fixed 5-percentage-point threshold and fires in 22–43% of runs even for strong true features. Interval coverage differences on a few dozen cases are noisy, so this rule is the main source of lost power. See the `warning_rate:*` columns.

## Screening stage (`screening_power.csv`)

Same 12-lag search as the original null experiment, with lag 2 made truly predictive (200 replicates):

| effect | naive "any lag p ≤ 0.05" | honest: any lag eligible | honest: true lag eligible |
| --- | ---: | ---: | ---: |
| 0 | 0.41 | 0.00 | 0.00 |
| 0.25 | 0.55 | 0.00 | 0.00 |
| 0.5 | 0.84 | 0.00 | 0.00 |
| 1.0 | 1.00 | 0.00 | 0.00 |

**The screening stage cannot release a single true lag at this sample size.** The circular-shift p-value is at least `1/n` (n − 1 shifts). With n = 46 the floor is 0.0217. Benjamini–Hochberg across 12 candidates then requires the smallest p-value to be at most 0.05/12 ≈ 0.0042. This holds even for a perfectly correlated feature, which gets an adjusted p of 0.26. A lone true lag can only pass with at least `20 × m` usable rows (240 for m = 12 candidates).

So the existing "0 of 40 null features promoted" result is guaranteed by this floor, not earned by discrimination. Ways to fix it, all open design decisions:

- register fewer candidates, so m is smaller;
- screen on a longer development window;
- replace the circular-shift null with one whose resolution does not depend on n (for example a block-permutation null with many draws).

## Limits

- One data-generating process, Gaussian noise, and a linear true effect. Real outbreaks are heavier-tailed.
- Monte Carlo standard error per gate cell is about 0.02 (500 replicates).
- The confirmation-window and audit-evidence gates are assumed to pass. This study measures only the statistical rules.
