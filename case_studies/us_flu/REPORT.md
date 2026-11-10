# US ILINet + Wikipedia: results

Design, data and frozen rules: [confirmation/README.md](confirmation/README.md). The registration (`ada9343c…54dc`) was pushed in commit `7599b56` before any confirmation forecast was scored.

## Registered decision (confirmation, 2024/25–2025/26)

**`rejected`.** Every audit check passed, including origin-level availability and vintage evidence, protocol registration and decision-code pins.

| | value |
| --- | ---: |
| Scored cases / origins | 1408 / 64 |
| Mean WIS difference (wiki − ar) | +0.0018 |
| Origin-bootstrap 95% interval | −0.0023 to +0.0065 |
| Origins where wiki helped | 48% |
| Warnings | `event_concentration`, `fewer_than_60_percent_origins_improved`, `uncertainty_includes_no_improvement` |

Positive differences mean the candidate is worse. Adding Wikipedia "Influenza" pageviews did not improve forecasts at either horizon (h=1: +0.0008, h=2: +0.0029). It helped in 3 of 11 regions, which is no better than chance. The development seasons showed the same pattern: +0.0032 overall, `rejected`. This is a **well-supported null** within the stated limits: 64 origins is well beyond the about 12 that the [power study](../synthetic_power/REPORT.md) flags as too few, so a large real effect would probably have shown up.

## Vintage optimism (descriptive)

Here the same models are trained and scored on latest-revised history instead of what was known at each release. WIS(latest-revised) − WIS(as-of):

| Split | `ar` | `ar_wiki` |
| --- | ---: | ---: |
| Development 2022/23–2023/24 | −0.0176 (−6.2%) | −0.0177 (−6.2%) |
| Confirmation 2024/25–2025/26 | −0.0074 (−1.9%) | −0.0077 (−2.0%) |

With source-native vintages, a standard retrospective backtest overstates skill by 2–6% in WIS. The gap is about the same for both models, so in this case it does not change which model wins. In the dengue pilot, where the evidence was Git-state, it did change the result.

## Metrics

| Split | Method | WIS | MAE | 80% cov. | 95% cov. |
| --- | --- | ---: | ---: | ---: | ---: |
| Development | ar | 0.2845 | 0.4374 | 0.788 | 0.866 |
| | ar_wiki | 0.2877 | 0.4373 | 0.787 | 0.866 |
| Confirmation | ar | 0.3826 | 0.5474 | 0.773 | 0.835 |
| | ar_wiki | 0.3844 | 0.5513 | 0.770 | 0.831 |

Both models under-cover (95% intervals reach only 83–87%). This was flagged in development and kept on purpose.

## Limitations

- This is a sealed retrospective: the data were public before registration, and the analyst knew in general terms how the seasons went.
- There is one pageview article in one language, and the model is a small ridge. A null here says nothing about richer digital-trace models.
- Truth is the archive as fetched on 2026-11-10. 2025/26 values may still change slightly.
- The October–November 2025 reporting gap (US federal shutdown) removed about 7 origins, as it did in real time.

Artifacts: `development/` and `confirmation_results/` (predictions, availability, receipt), plus `confirmation_results/assessment/`, the registered evidence bundle. `honestforecast verify` passes on it.
