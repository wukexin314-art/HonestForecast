# US ILINet + Wikipedia: sealed retrospective confirmation (registered 2026-11-10)

**Question:** do weekly English Wikipedia "Influenza" pageviews (`wikipedia_influenza`) improve a ridge forecast built only from as-of wILI history (`ar`), 1 and 2 weeks ahead, for the US and the 10 HHS regions?

Registration digest (`registration_sha256` in `protocol.lock.json`):

```
ada9343c4f0e6397fca74ced1f764368e6897ba18fcad45f43ce42b7b99554dc
```

This is a **sealed retrospective**, not a prospective study. All confirmation data were already public when the design was locked, but no confirmation-season forecast had been scored. The commit that adds this folder, the pipeline and the development results is pushed before the confirmation run, so the Git history shows the order. The lock also pins the decision-code hashes (schema 1.1).

## Data (source-native vintages)

- **Target history**: Delphi V5 archive of CDC ILINet `wili` (`source=fluview_ilinet`, nation and HHS). Each row is one value change, stamped with its real release date. Stored in `../data/fluview_wili_revisions.csv` (reference weeks 2019-07 to 2026-09, fetched 2026-11-10).
- **Candidate feature**: Wikimedia REST pageviews for `en.wikipedia/Influenza`, user agent only, summed over MMWR weeks (Sunday to Saturday). Treated as never revised and complete 2 days after the week ends.
- **Truth**: the latest-revised value in that archive as fetched. Values for 2025/26 may still receive small late revisions.

## Frozen design

| Item | Value |
| --- | --- |
| Origins | Every national ILINet release date from October to May |
| Development | Seasons 2022/23 and 2023/24 (used for pipeline checks only; nothing was tuned) |
| Confirmation window | Origins 2024-10-01 to 2026-05-31 (seasons 2024/25 and 2025/26) |
| Units | `nat`, `hhs1`–`hhs10`; bootstrap resamples origins, pooling units |
| Baseline `ar` | Direct h-step ridge on wILI at weeks t and t−1 plus annual sine/cosine of the target date. Trained on the previous 156 weeks as known at the origin |
| Candidate `ar_wiki` | Baseline plus log(1 + weekly pageviews at week t) |
| Intervals | Gaussian from the training residual spread, floored at 0 |
| Horizons / metric | 1 and 2 weeks / paired WIS. Promotion needs no registered warning (`docs/assessment.md`) |
| Bootstrap / seed | 1000 / 20261109 |
| Code | `src/honestforecast/flu_case.py` at the registration commit, plus the lock-pinned decision modules |
| Secondary (descriptive) | Vintage optimism = WIS(latest-revised history) − WIS(as-of history), for both models; region breakdown |

## Rules fixed in advance

1. One registered `assess` run on the confirmation split. No change to the model, features, split or rules afterwards.
2. Missing releases are not backfilled. CDC published nothing between 2025-09-26 and 2025-11-14 (the US federal shutdown), so those weeks have no origins, as happened in real time.
3. A case is scored only if every method can produce it, so all prediction grids match exactly.
4. The result is reported whatever it is, together with the development result and the power caveats in `../../synthetic_power/REPORT.md`.

## Known weaknesses kept on purpose

- Development 95% interval coverage was about 0.87, so the Gaussian intervals are too narrow. This affects both models equally and was not tuned away.
- The training window reaches into the COVID-disrupted 2020/21 and 2021/22 seasons.
- Wikipedia "Influenza" views reflect media attention as well as illness.

## Reproduce

```bash
honestforecast-flu-case fetch   # optional: refetch; results will differ slightly if CDC revised since 2026-11-10
honestforecast-flu-case run --split confirmation --output-dir build/flu-confirmation
honestforecast assess \
  --contract case_studies/us_flu/confirmation/forecast_contract.json \
  --manifest case_studies/us_flu/confirmation/feature_manifest.csv \
  --baseline build/flu-confirmation/predictions_ar.csv \
  --candidate build/flu-confirmation/predictions_ar_wiki.csv \
  --availability build/flu-confirmation/availability.csv \
  --candidate-id wikipedia_influenza --candidate-kind feature \
  --registration case_studies/us_flu/confirmation/protocol.lock.json \
  --all-audit-gates-passed --output build/flu-assessment
```
