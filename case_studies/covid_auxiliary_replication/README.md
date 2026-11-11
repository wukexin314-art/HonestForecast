# Registered out-of-period replication: do COVID-19 auxiliary indicators improve HRR case forecasts?

Status: **registered 2026-11-11, before any confirmation-window data were fetched** (locks below). During the feasibility check (2026-11-10), two as-of snapshots (issued 2021-03-16 and 2021-11-16) were fetched for each signal. Only row counts, HRR counts and lags were printed. No values were inspected. No confirmation-window forecast has been produced or scored.

## Claim under test

McDonald et al. (2021), *PNAS* 118(51):e2111453118, report that adding each of five auxiliary indicators to an autoregressive quantile-regression model improves the average WIS of 7–21-day-ahead HRR case-rate forecasts. Their forecast dates run from 2020-06-09 to 2020-12-31; the replication code runs to 2021-03-31. A 2026 correction changed only a competing-interest disclosure.

This study freezes their published specification and tests the claim on origins **after** every date their code used. For CHNG and Google-AA, it is also the first test on genuine as-of data. Their CHNG inputs before 2021-02-22 were estimates, and their Google inputs were finalized values.

Evidence label: **sealed retrospective.** All data are public, and the analysts know the broad course of 2021 (Alpha, Delta, Omicron). No forecast in the confirmation window has been scored.

## Frozen specification (copied from `cmu-delphi/covidcast-pnas`, `forecast/code/`)

| Item | Value | Source |
| --- | --- | --- |
| Target | `jhu-csse/confirmed_7dav_incidence_prop` at HRR level, as a level (no transform) | `train_signals.R` |
| Baseline `AR3` | Linear quantile regression on target lags 0, 7 and 14 days, with an intercept | paper Methods; `pkgs_and_common.R` |
| Candidates | `AR3` plus the indicator at lags 0, 7 and 14 | `train_signals.R` |
| Indicators | `chng/smoothed_adj_outpatient_cli`, `chng/smoothed_adj_outpatient_covid`, `doctor-visits/smoothed_adj_cli`, `fb-survey/smoothed_hh_cmnty_cli`, `google-symptoms/sum_anosmia_ageusia_smoothed_search` (missing values set to zero, as in `AR3GSSAA3_Zero`) | `train_signals.R` |
| Quantiles | 0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975; no penalty (λ = 0); crossings fixed by post hoc sorting | `quantgen.R` |
| Training | Latest 21 days with an observed response, all HRRs pooled, no location effects. Refit per forecast date and per horizon | `quantgen.R` |
| Features at prediction | Latest non-missing value of each feature as of the forecast date | `make_newx` |
| Data | As-of snapshot at each forecast date (Delphi `as_of`) | `download_signals.R` |

Checked against the source on 2026-11-11 (`pkgs_and_common.R`, `qr_forecast/train_signals.R`, `qr_forecast/quantgen.R`, and `covidcast::aggregate_signals` / `apply_shifts_one`):
- Daily forecast dates `seq(2020-06-09, 2021-03-31, by = "day")`, `ntrain = 21`, `ahead = 7:21`, lags `c(0, 7, 14)`, `lambda = 0`, `sort = TRUE`, the seven quantiles, and the five signals listed above, with zero imputation only for `AR3GSSAA3_Zero`.
- Prediction row: `make_newx` takes each lagged column's latest non-missing date. `apply_shifts_one` shifts only within each HRR's observed date range, so this equals the indicator's lags 0, 7 and 14 at its latest date, as implemented here.
- Training end: `min(feature_end_date, response_end_date)`, where `feature_end_date` is the latest date in the joined feature frame. At these indicator latencies this equals the last observed response date minus the horizon, as here. Rows with a missing feature are dropped here; the original passes them to `quantile_lasso`, which did not arise in development.

## Deviations, fixed before any confirmation data are seen

1. **Forecast dates are daily, as in their code. Horizons are 7, 14 and 21 days** instead of 7–21. The model is unchanged.
2. **Window: every day from Monday 2021-04-05 to Sunday 2022-01-16**, 287 forecast dates in 41 complete weeks. The end is set by Google-AA, which ends on 2022-01-20.
2a. **Resampling unit = forecast week.** The `origin` column holds the Sunday that ends the forecast week, and `forecast_date` holds the real forecast date. Neighbouring days share targets for up to 21 days. With 287 daily units, the pinned bootstrap would use 7-day blocks and understate uncertainty. With 41 weekly units it uses blocks of round(41^(1/3)) = 3 weeks, which is at least the longest horizon.
3. **CHNG pause.** The CHNG pipeline paused from 2021-10-08 to 2021-12-02. A CHNG origin is scored only if a CHNG value issued within the 14 days before the forecast date exists for at least 90% of HRRs. Missed origins are not backfilled. This rule is the same for both CHNG indicators.
3a. **Pairing.** For each indicator, a case is scored only if both `AR3` and the indicator model produced it. Every dropped case is counted in `pairing_log.json`. An indicator is `incomplete` if fewer than 80% of the planned weeks are scored.
3b. **Availability evidence** is recorded per week and HRR: the latest source date the indicator model used on any day of that week. A zero-imputed Google value has no source date. The zero is decided at the forecast date, so that date is recorded, and the number of imputed cases is reported.
4. **Low-count filter.** As in their supplement (`fd_casefloor = 30`), a case is dropped when the HRR's 7-day case count at the forecast date is below 30, as known at the forecast date. The jump filter (`flag_jumps`) is not reproduced, because its rule is defined in a file we did not read. Dropped cases are dropped for both methods.
5. **Truth** is the target as of the fetch date (expected 2026-11), not 2021-05-18.
6. **CTIS signal:** `fb-survey/smoothed_hh_cmnty_cli` (unweighted), as in their code. Check that it is served for 2021-04 to 2022-01 before registration; if it is not, use `smoothed_whh_cmnty_cli` and record the substitution.

## Development (allowed, before registration)

Reproduce their headline period (daily forecast dates from 2020-06-15 to 2020-12-27, 28 weeks, same horizons) with the as-of data available for that period. The purpose is to check the reimplementation, not to tune it. Success criterion, fixed now: `AR3` beats the flat-line baseline on average WIS, and at least three of the five indicators improve on `AR3`, matching the paper's direction. If the reproduction fails, the implementation is debugged on 2020 data only. The confirmation window is never used for debugging.

After development, the model code's sha256 is recorded in this folder's README and a test checks it, as in `us_flu_nowcast`.

### Development findings so far (weekly-origin pilot, 29 Mondays)

The weekly pilot met the success criterion: 4 of 5 indicators improved on `AR3`, CHNG-CLI was about equal (as the paper reported for forecasting), and Google-AA had almost no vintages before September 2020. But the block-bootstrap half-widths were 2–5% of `AR3` WIS (7.23), against gains of 0.4–2.6%. Only CTIS's unadjusted interval excluded zero, and no indicator passed Holm. A 42-origin weekly confirmation would mainly have measured its own low power, so the design moved to daily forecast dates with weekly resampling units (deviations 1–2a). The daily development results are recorded below before registration.

### Development results (daily forecast dates, 2020-06-15 to 2020-12-27, 28 weeks, as-of data)

| Indicator | Weeks | Mean WIS diff vs `AR3` | Block-bootstrap 95% CI | Half-width (% of `AR3` WIS) | Holm p |
| --- | --- | --- | --- | --- | --- |
| CHNG-CLI | 28 | −0.015 (−0.2%) | (−0.260, +0.229) | 3.4% | 1.000 |
| CHNG-COVID | 28 | −0.135 (−1.9%) | (−0.480, +0.164) | 4.5% | 0.912 |
| DV-CLI | 28 | −0.036 (−0.5%) | (−0.217, +0.100) | 2.2% | 1.000 |
| CTIS-CLI-in-community | 28 | −0.194 (−2.7%) | (−0.390, −0.021) | 2.6% | 0.095 |
| Google-AA (zero-imputed) | 4 | +0.297 (+3.2%) | (−0.020, +0.614) | 3.4% | 1.000 |

- Success criterion: met. `AR3` beats the flat line at 7 and 14 days (WIS ratio 0.88 and 0.93) but not at 21 days (1.03). Four of five indicators have a negative mean difference. Google-AA has as-of vintages for only 4 weeks of 2020, so its development result is uninformative.
- Power: daily dates did **not** materially narrow the intervals, because the resampling unit is still the week and week-to-week variation dominates. With 41 confirmation weeks, the expected half-widths are about √(28/41) ≈ 0.83 times these, i.e. **about 2–4% of `AR3` WIS**. Gains smaller than that will be reported as not distinguishable from zero. Under Holm, only a gain of roughly 3–5% would replicate.
- No setting was changed after seeing these results.

## Registered analysis

- One `honestforecast assess` per indicator against `AR3`. Units are HRRs, horizons are 7, 14 and 21 days, and each indicator has its own lock. A single folder holds all five, registered in the same commit.
- **Primary quantity** per indicator: paired mean WIS difference with its origin block-bootstrap 95% interval, and the improvement it rules out as a percentage of `AR3` WIS.
- **Replication criterion** (fixed now): the published claim "replicates" for an indicator if the mean WIS difference is negative and the block-bootstrap upper bound is below zero. Gate states (`promoted` / `challenger` / `rejected`) are reported alongside but are not the replication criterion, because the gates add robustness rules that the original paper did not use.
- **Multiplicity:** five indicators, with each interval reported unadjusted and with a Holm adjustment across the five. The headline is the number of indicators that replicate under Holm.
- **Registered stratum:** `trend` = rising/flat/falling at the origin, defined by the target's 7-day relative change as known at the origin (above +10%, between −10% and +10%, below −10%). This tests the paper's secondary claim that gains are largest when cases are flat or falling.
- **Secondary, descriptive:** vintage optimism. Rerun every model on finalized data and report the WIS gap per indicator, and whether the ranking changes. The paper's supplement found finalized results up to about 10% better and a different ranking.

## Interpretation fixed in advance

- A failure to replicate applies to this specification in 2021–22. It is not a claim that the indicators never help.
- Power: the development intervals give the smallest gain this design can resolve. Gains below that are reported as not distinguishable from zero, not as evidence of no effect.
- If more than 20% of planned origins are unscorable for an indicator, its result is reported as `incomplete`.

## Decisions (2026-11-11)

1. Origins: weekly Mondays, three horizons. Revised after the weekly development pilot to daily forecast dates with weekly resampling units.
2. Replication criterion: mean WIS difference below zero and block-bootstrap upper bound below zero, with Holm across the five indicators.
3. Window: common to all five indicators, 2021-04 to 2022-01.

## Registration (2026-11-11)

One lock per indicator in `confirmation/`, all with confirmation window 2021-04-05 to 2022-01-16 (origin labels are the Sundays 2021-04-11 to 2022-01-16):

| Indicator | Lock | `registration_sha256` |
| --- | --- | --- |
| CHNG-CLI | `protocol_chng_cli.lock.json` | `a5566d7f6dd7be0ab4430c467089adcdf6fe7938107cb82396e5ef578fba4be5` |
| CHNG-COVID | `protocol_chng_covid.lock.json` | `1d97b83d7742d938a4155e4a14c0a0079684bb42d96ea2b394d0197179edb0da` |
| CTIS-CLI-in-community | `protocol_ctis_cmnty_cli.lock.json` | `ff677681334379b4477afb7dc559cdfe458f8ca7e2023581d3fe338756a1ba41` |
| DV-CLI | `protocol_dv_cli.lock.json` | `4f3e36f070e5bfdd33a1840a965cf9c9b3f50e1f20b38ce34d234c3aebc0ed91` |
| Google-AA | `protocol_gs_anosmia_ageusia.lock.json` | `ef4f7dcffdaf0d57e58ca04b17758cc4fdcf640fad7e42e5e68127f2ee4a9d60` |

The model code is outside the locks. Its hash is recorded here and checked by `tests/test_case_study_artifacts.py`:

- `replicate.py`: `e0116b3daa212b2459d3c1b9f7053dfaa9903d2e681bcc96cac7a83fe3b8d9b7`

The lock timestamps come from the local clock. The external timestamp is the public Git commit that adds this folder, made before any confirmation-window fetch.

## Running the confirmation (after registration only)

Requires `numpy`, `scipy` and a Delphi API key in `DELPHI_EPIDATA_KEY` or `~/.config/delphi/key`. Raw Delphi data are cached under `build/` and are not committed (CHNG is CC BY-NC; Google Symptoms has its own terms).

From the repository root (outputs default to `build/covid_confirmation_<data>[_paired]`):

```bash
S=case_studies/covid_auxiliary_replication
python $S/replicate.py fetch --split confirmation
python $S/replicate.py run --split confirmation --data asof
python $S/replicate.py prepare --split confirmation --data asof
```

Then, for each indicator `<i>`, run `honestforecast assess` on `build/covid_confirmation_asof_paired/<i>/` with `--contract $S/confirmation/forecast_contract.json --manifest $S/confirmation/feature_manifest.csv --registration $S/confirmation/protocol_<i>.lock.json --candidate-id <i> --candidate-kind feature --stratum trend`, then `python $S/replicate.py holm --split confirmation --data asof`. Repeating with `--data finalized` gives the secondary vintage-optimism analysis.
