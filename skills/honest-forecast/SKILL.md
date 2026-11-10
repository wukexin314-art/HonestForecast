---
name: honest-forecast
description: Register, audit, and verify whether a feature, data source, model, preprocessing, recalibration, ensemble, or pipeline change deserves admission to a time-series forecast. Use for point-in-time validity, revised or delayed data, locked confirmation designs, paired probabilistic comparison, subgroup robustness, power-aware interpretation of rejections, promotion decisions, and evidence bundles; do not use merely to fit or tune an ordinary forecasting model.
---

# Honest Forecast

Use the HonestForecast Python package as the calculation and validation layer. The skill guides the evidence workflow; it must not reproduce scoring logic in prose or relax a failed gate to obtain a favorable result.

## Workflow

1. Identify the forecast origin, target date, horizon, outcome-maturity rule, baseline, candidate ID and kind, and the evidence label. Use `prospective` only when no confirmation outcome existed at registration. Use `sealed retrospective` when the data were public but no confirmation forecast had been scored. Use `exploratory` otherwise. Do not infer a prospective design from historical files.
2. Check the candidate's design before testing it. If the candidate's value is timeliness (digital traces, early reports), confirm that the features use what is available at the origin but not yet in the target history. A same-week copy of a timely signal tests the wrong question. Enter drifting sources as ratios or growth rather than raw levels. When source vintages exist, also run each model on latest-revised history as a diagnostic of vintage optimism.
3. Inspect or create the forecast contract and paired predictions. For `feature` and `data_source` candidates, also require a feature manifest; other kinds must not receive invented feature provenance. Read [references/assessment-schema.md](references/assessment-schema.md) when preparing or repairing inputs.
4. Select and tune only on development data. Record every variant tried, with its development result, and choose with a rule stated before looking and independent of whether it favors the candidate (for example, the lowest absolute candidate WIS on a common grid). Report the variants that lost.
5. Before a promotion-capable confirmation run, create the protocol and run `honestforecast register`. Schema 1.1 locks pin the decision code (`assessment`, `audit`, `comparison`, `metrics`). Pin the model or pipeline code too, for example by recording its sha256 beside the lock and testing it. Do not edit any pinned file while a confirmation is open. Publish the lock through a dated push, tag or registry before outcomes are scored; the local timestamp is not trusted.
6. Ask for origin-level availability evidence when a feature or data-source candidate needs a leakage-safe promotion claim. For other candidate kinds claiming all gates passed, require structured audit evidence whose check IDs match the protocol and whose artifacts match their hashes. Never invent provenance, timestamps, evidence, or checks.
7. Run `honestforecast assess` on the supplied artifacts, once per registered confirmation. Use the local package source or installed command already available in the environment. Installing software or retrieving data requires the same authorization it would outside this skill.
8. If validation fails, report the invalid or incomparable evidence and correct only genuine data-format errors within scope. Do not intersect unequal grids silently, repair crossing quantiles by sorting them, backfill missed releases, replace missing vintages with current values, or change registered settings.
9. Run `honestforecast verify` on the evidence bundle, supplying available original inputs so their recorded hashes are checked. Review `audit_receipt.json`, `origin_differences.csv`, `robustness.json`, and `evidence_card.md`. Read [references/promotion-gates.md](references/promotion-gates.md) before interpreting a decision or advising one.
10. Preserve `decision_log.jsonl`, including rejected and challenger results. A new analysis version appends a decision or a new registration folder; it does not erase an unfavorable one. Superseding a lock is allowed only before its first confirmation origin, and the old lock stays.

## Required boundaries

- Compare baseline and candidate on identical `(origin, target_date, horizon, unit)` keys and identical actual values.
- Treat candidate-minus-baseline WIS and MAE below zero as improvement.
- Outcomes already inspected cannot become confirmation evidence later. A redesigned candidate needs new confirmation data, not the seasons that motivated the redesign.
- A `promoted` label requires a matching protocol lock, explicit audit-gate confirmation, and no registered horizon or stratum warning. Feature and data-source candidates additionally require origin-level availability evidence; other kinds require hash-verified structured audit artifacts.
- Describe a rejection as applying to the tested candidate representation, not every possible use of its source, feature, or model family. State its power: the number of scored origins and the smallest improvement the bootstrap interval rules out.
- Subgroup or period breakdowns that were not registered are descriptive only.
- Keep patient-level, identifiable, restricted, credential-bearing, or unclear-license artifacts out of public outputs. Aggregate predictions are not automatically public-safe; inspect their disclosure risk. Run the repository's safety scan and tests as their own step and stop on failure before any commit or push.
- Treat the evidence card as conditional on the supplied provenance. It is not a causal, clinical, or deployment-safety claim.

## Deliverable

Return the candidate ID and kind, evidence label, registration and verification status, and decision state. Give the paired WIS and MAE differences, the origin-bootstrap interval and the improvement it rules out (lower bound as a percentage of baseline WIS), and the number of scored origins. Add the proportion of improved origins, coverage change, any horizon or registered-stratum warnings, failed or missing audit checks, the vintage-optimism gap when measured, development variants tried, and the paths to generated evidence. Lead with invalidity or missing provenance before discussing favorable metrics.
