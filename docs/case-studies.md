# Case studies and provenance

HonestForecast was distilled from three applied forecasting projects. Only the India dengue example is included as a reproducible public case. The other two are described at a deliberately high level because their source projects have data-sharing or client restrictions.

## India dengue nowcasting — public example

The project combined delayed monthly surveillance outcomes with Google Trends and Wikipedia proxy signals. The HonestForecast pilot reconstructed the values preserved in Git at each historical forecast origin and compared seasonal-naive, target-history ridge, and digital-proxy ridge forecasts on the same seven targets.

Main findings:

- the source repository preserved 18 usable data states;
- frequently refreshed digital series repeatedly rewrote historical values;
- seasonal naive had lower MAE and WIS than both ridge challengers in the short pilot;
- replacing origin-matched proxies with latest-revised histories materially changed the measured performance;
- neither feature increment passed promotion gates.

This is evidence that vintage handling can change a feature conclusion, not evidence that one model is generally best or that digital indicators are generally useless.

## Pediatric healthcare demand forecasting — restricted source project

This project studied daily and sub-daily operational demand forecasting using aggregate healthcare counts, calendar structure, respiratory surveillance, weather, and other external indicators. It motivated the fold-local feature pipeline, explicit availability rules, rolling-origin evaluation, and the distinction between a promising challenger and a confirmed replacement.

Public-safe lessons:

- complex models did not consistently beat strong seasonal and ensemble baselines;
- some structural or public-health feature sets produced small target-specific improvements, but uncertainty often included no improvement;
- a variable that explains historical regime changes is not automatically useful for a future forecast;
- aggregate totals could not distinguish demand, case mix, severity, routing, and recording changes;
- additional feature searches were less valuable than better-defined operational data and another untouched evaluation period.

No healthcare records, institution-specific data, exact internal tables, or source-project code are included here.

## Electricity-market decision forecasting — internal source project

This project evaluated whether issue-time market, system, and weather forecasts could improve a day-ahead versus real-time decision under a strict operational cutoff. It motivated vintage manifests, decision-aware evaluation, event-concentration checks, prospective freezing, and the rule that predictive accuracy and economic value must be evaluated separately.

Public-safe lessons:

- point-in-time forecast features could describe system stress without producing a stable decision advantage;
- apparent post-hoc feature gains did not necessarily survive an untouched prospective period;
- rare events could dominate average results and required drop-best-event and block-bootstrap checks;
- an event-warning model was not interchangeable with an optimal action policy;
- a strong simple benchmark remained preferable when candidate gains were small or unstable.

No client identity, credentials, private load data, monetary result, internal code, or deployable policy is disclosed here.

## What was transferred

Only general research controls were transferred into HonestForecast:

- explicit issue-time and outcome-maturity contracts;
- versioned feature manifests and as-of joins;
- fold-local transformations;
- identical-grid ablation;
- probabilistic and decision-aware metrics;
- block/bootstrap and event-concentration sensitivity;
- frozen confirmation before promotion;
- preservation of negative results.
