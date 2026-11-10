# India dengue prospective confirmation (registered 2026-11-10)

> **Superseded by [v2](../prospective_v2/README.md) on 2026-11-10, before any in-window origin.** The design is unchanged. v2's lock also pins the decision-code hashes. Use v2 for scoring.

This folder freezes the confirmatory test of the question the pilot could not settle: **do digital-proxy features (`digital_proxies`) improve the target-history ridge (`ar`) on origins captured after this registration?**

Registration digest (`registration_sha256` in `protocol.lock.json`):

```
cb21d3eb0fd6d7ace1faf2d13a4bd5990e90eb00cb0f4d4966d8bf5e9969935f
```

The lock's own timestamp comes from a local clock and is not trusted. The trusted date is the GitHub push of the commit that adds this folder. Any later edit to `protocol.json`, `forecast_contract.json` or the lock makes `assess --registration` fail (a test checks this).

## Frozen design

| Item | Value |
| --- | --- |
| Data | `dengue_updater/data/processed/monthly_data.csv` in `wukexin314-art/Nowcast-Dengue-in-India`, one Git snapshot per scheduled update (5th and 20th) |
| Origin | Commit date of the first snapshot that has Google Trends for the target month and no WHO value yet (`_eligible_origins`, unchanged) |
| Confirmation window | Origins dated 2026-11-10 to 2027-11-10, about 12 target months (2026-11 to 2027-10) |
| Baseline | `ar`: ridge on log cases 12 months earlier plus month-of-year terms |
| Candidate | `ar_digital_asof`: baseline plus the four as-of features in `feature_manifest.csv` |
| Horizon / metric | 1 month / paired WIS. Decision rules are the registered warnings in `docs/assessment.md` |
| Bootstrap / seed | 1000 / 20261109 |
| Model code | `src/honestforecast/dengue_case.py` at the registration commit |
| Secondary (descriptive only) | `ar` vs `seasonal_naive`, and latest-revised minus as-of WIS |

## Rules fixed in advance

1. One registered assessment, run after the last window target has a WHO value. No interim decision. Progress reports may count captured origins but do not open scores.
2. A failed or missing scheduled snapshot is not backfilled. If its target first appears in a later snapshot, that later snapshot is the origin, exactly as the code already does.
3. If fewer than 6 targets are scored at the end of the window, the result is reported as `incomplete`. The window is not extended.
4. Fewer than 12 scored targets is reported as such, alongside the power numbers below.
5. A design change before the first in-window origin (2026-11-20) needs a new lock and a new folder. This one stays. After that date, no changes are allowed.

## Why 12 targets, and what to expect

The [synthetic power study](../../synthetic_power/REPORT.md) shows that with 6 origins and 2 horizons, the gate releases a null feature 13% of the time and a strong feature only 45% of the time. This study has 1 horizon, so 12 targets give about the same number of paired cases as that 6-origin row. **Even a real, strong improvement has roughly a coin-flip chance of being promoted.** A `rejected` or `challenger` result here is weak evidence against digital proxies, not proof that they do not help.

Known weakness kept on purpose: intervals use in-sample residual quantiles (see the pilot). It is frozen as-is so that the confirmation tests the design that was actually piloted.

## How to score (after outcomes mature, about January 2028)

```bash
honestforecast-dengue-pilot --repo ../Nowcast-Dengue-in-India \
  --origin-start 2026-11-10 --output-dir build/prospective
honestforecast assess \
  --contract case_studies/india_dengue/prospective/forecast_contract.json \
  --manifest case_studies/india_dengue/prospective/feature_manifest.csv \
  --baseline build/prospective/predictions_ar.csv \
  --candidate build/prospective/predictions_ar_digital_asof.csv \
  --availability build/prospective/availability.csv \
  --candidate-id digital_proxies --candidate-kind feature \
  --registration case_studies/india_dengue/prospective/protocol.lock.json \
  --all-audit-gates-passed --output build/prospective-assessment
```

Origins after 2027-11-10 must be dropped before `assess`, because it rejects origins outside the window. A dry run of these commands on the pilot origins, with a throwaway lock, passed every audit check on 2026-11-09.
