# US ILINet + Wikipedia nowcast v2: prospective 2026/27 (registered 2026-11-10)

**Question:** do the Sunday–Wednesday English Wikipedia "Influenza" pageviews of the current week improve a ridge forecast built only from as-of wILI history, 1 and 2 weeks ahead? These pageviews already exist when Friday's ILINet release covers only last week.

This follows the [v1 sealed retrospective](../us_flu/REPORT.md), which ruled out gains above about 1.1% for same-week pageviews (0.6% under the original iid bootstrap). v2 changes four things:

1. It uses the feature's **timeliness**: the partial current week, which v1 never used.
2. It enters pageviews as **growth** (partial-week rate vs the last full week), so traffic drift cancels.
3. It sets interval spread from each method's own **out-of-sample errors**, scored against values released by the origin.
4. It registers an **activity stratum** (as-of wILI ≥ 3 at the origin). A loss in either the high or the low group that is distinguishable from the pooled gain blocks promotion.

Registration digest (`registration_sha256` in `prospective_r3/protocol.lock.json`):

```
e941a93407fac9f919d236324f1bf01b8744508510b592d3a5b37aabce7aaf7d
```

This lock supersedes two earlier locks registered the same day, before the first confirmation origin: `prospective/` (`ee5dc3b3e549de81e00db5a65d061aa1eb6bae155a0e84770413acbf0915220a`) and `prospective_r2/` (`3c44ec850a0d7e705e29e6a11d0fa20039b28cd0e4a083626224abac128cf83d`). The design, contract and manifest are byte-identical in all three. Only the pinned decision code changed: r2 made the origin bootstrap a circular block bootstrap, because neighbouring weekly origins are autocorrelated; r3 also requires evidence beyond noise before the coverage, horizon or stratum rules can veto (see `skills/honest-forecast/references/promotion-gates.md`). The old folders are kept.

**This is a true prospective test.** Confirmation origins are ILINet releases from **2026-11-13** (the first release after this folder was pushed) to 2027-05-31. None of their outcomes existed at registration.

An independent timestamp comes from Zenodo: release `v0.8.0` (commit `e11b309`), which contains this lock, was archived as [10.5281/zenodo.24122438](https://doi.org/10.5281/zenodo.24122438) at 2026-11-11 00:44 UTC, before the first confirmation origin. The archived lock digest and decision code match this folder byte for byte.

## Pinned model code

The lock pins the decision modules. The model code is pinned here, and `tests/test_case_study_artifacts.py` fails if any of it changes:

| File | sha256 |
| --- | --- |
| `src/honestforecast/flu_nowcast.py` | `e6a94d37e0c45a2535858027f8dc2bb4f60692cc2229dd0ec622f9bb31628da3` |
| `src/honestforecast/flu_case.py` | `e8bfca4081071490657a079f4a99903ab48c11a85f97becd17f9fc2661be1ff5` |
| `src/honestforecast/dengue_case.py` | `1dc685cd53b2d2a10fc9d6405eab52413d6a4e324463cd1de043a4f9acafbd9e` |

## Development (2022/23–2025/26): every variant tried

All variants were run on development seasons only. 2926 paired cases (133 origins × 11 regions × 2 horizons) unless noted. WIS difference = candidate − baseline, so positive means worse.

| Variant | Features | Training window | Baseline WIS | Candidate WIS | Difference (95% CI) | Origins improved |
| --- | --- | --- | ---: | ---: | --- | ---: |
| A | growth + level vs trailing year | full 156 weeks | 0.3461 | 0.3653 | +0.0192 (+0.0059, +0.0332) | 33% |
| **B (frozen)** | **growth only** | **full 156 weeks** | **0.3461** | **0.3472** | **+0.0011 (−0.0016, +0.0040)** | **46%** |
| C | growth + level | COVID weeks 2020-03..2022-06 dropped | 0.3134 | 0.3155 | +0.0020 (−0.0069, +0.0103), 2530 cases | 43% |
| D | growth only | COVID weeks dropped | 0.3859 | 0.3846 | −0.0014 (−0.0034, +0.0008) | 60% |

**Selection rule**, chosen before picking and independent of the sign of the difference: take the lowest absolute candidate WIS on the common 2926-case grid. That is the system a forecaster would actually deploy. This gives **B**. C is on a different grid. D was the only variant favorable to Wikipedia, but its baseline is 11% worse, so choosing it would have been selection on the result.

B in development: activity high +0.0018, low +0.0005; h=1 +0.0021, h=2 +0.0001. Calibration improved over v1: baseline 80% coverage 0.84 and 95% coverage 0.90, up from 0.79 and 0.87.

The growth feature does carry signal. Its correlation with next-week national wILI growth is 0.22–0.28 in every period since 2020. In the development seasons, that signal did not translate into better forecasts beyond the AR terms.

## Frozen design

| Item | Value |
| --- | --- |
| Data | Delphi V5 ILINet `wili` archive (real release dates) and Wikimedia daily pageviews for `en.wikipedia/Influenza` (user agent), in `data/` |
| Origins | National ILINet releases; forecasts made only when the Sunday–Wednesday views are complete (by Thursday) |
| Baseline `ar` | Direct ridge on wILI(t), wILI(t−1) and annual sine/cosine. Previous 156 weeks as known at the origin |
| Candidate `ar_wiki_nowcast` | Baseline plus log(mean daily views Sun–Wed of week t+1 ÷ mean daily views of week t) |
| Intervals | Gaussian with RMS of the method's last 52 resolved out-of-sample errors per region and horizon (at least 10, else the training spread). Calibration state warms up from 2022/23 |
| Stratum | `activity` = high if as-of wILI ≥ 3.0 at the origin |
| Horizons / metric | 1 and 2 weeks / paired WIS. Promotion needs no registered warning |
| Bootstrap / seed | 1000 / 20261109, circular block bootstrap over origins |

## Rules fixed in advance

1. One registered `assess` run after the last window target has been released and allowed to settle. Scoring is planned for about July 2027. No change to code, features or rules before then; the pinned hashes enforce this.
2. Missed CDC releases are not backfilled, as in v1.
3. A case is scored only if both methods can produce it.
4. Development predicts a likely `rejected` (B ≈ +0.3%). The result is reported whatever it is. With roughly 30 origins, the power study's caveats apply. An improvement smaller than about 1% is unlikely to pass.

## Score (July 2027)

```bash
honestforecast-flu-nowcast fetch
honestforecast-flu-nowcast run --split confirmation --output-dir build/nowcast-confirmation
honestforecast assess \
  --contract case_studies/us_flu_nowcast/prospective_r3/forecast_contract.json \
  --manifest case_studies/us_flu_nowcast/prospective_r3/feature_manifest.csv \
  --baseline build/nowcast-confirmation/predictions_ar.csv \
  --candidate build/nowcast-confirmation/predictions_ar_wiki_nowcast.csv \
  --availability build/nowcast-confirmation/availability.csv \
  --candidate-id wikipedia_influenza_nowcast --candidate-kind feature \
  --stratum activity \
  --registration case_studies/us_flu_nowcast/prospective_r3/protocol.lock.json \
  --all-audit-gates-passed --output build/nowcast-assessment
```
