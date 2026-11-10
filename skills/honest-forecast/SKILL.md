---
name: honest-forecast
description: Register, audit, and verify whether a feature, data source, model, preprocessing, recalibration, ensemble, or pipeline change deserves admission to a time-series forecast. Use for point-in-time validity, locked confirmation designs, paired probabilistic comparison, subgroup robustness, promotion decisions, and evidence bundles; do not use merely to fit or tune an ordinary forecasting model.
---

# Honest Forecast

Use the HonestForecast Python package as the calculation and validation layer. The skill guides the evidence workflow; it must not reproduce scoring logic in prose or relax a failed gate to obtain a favorable result.

## Workflow

1. Identify the forecast origin, target date, horizon, outcome-maturity rule, baseline, candidate ID and kind, and whether the result is development or frozen confirmation evidence. Do not infer a prospective design from historical files.
2. Inspect or create the forecast contract and paired predictions. For `feature` and `data_source` candidates, also require a feature manifest; other kinds must not receive invented feature provenance. Read [references/assessment-schema.md](references/assessment-schema.md) when preparing or repairing inputs.
3. Before a promotion-capable confirmation run, create the protocol and run `honestforecast register`. Do not describe a lock created after outcomes were inspected as prospective. Treat its local timestamp as untrusted unless its digest was published through an external dated system.
4. Ask for origin-level availability evidence when a feature or data-source candidate needs a leakage-safe promotion claim. For other candidate kinds claiming all gates passed, require structured audit evidence whose check IDs match the protocol and whose artifacts match their hashes. Never invent provenance, timestamps, evidence, or checks.
5. Run `honestforecast assess` on the supplied artifacts. Use the local package source or installed command already available in the environment. Installing software or retrieving data requires the same authorization it would outside this skill.
6. If validation fails, report the invalid or incomparable evidence and correct only genuine data-format errors within scope. Do not intersect unequal grids silently, repair crossing quantiles by sorting them, replace missing vintages with current values, or change registered settings.
7. Run `honestforecast verify` on the evidence bundle, supplying available original inputs so their recorded hashes are checked. Review `audit_receipt.json`, `origin_differences.csv`, `robustness.json`, and `evidence_card.md`. Read [references/promotion-gates.md](references/promotion-gates.md) before interpreting a promotion or advising a decision.
8. Preserve `decision_log.jsonl`, including rejected and challenger results. A new analysis version appends a decision; it does not erase an unfavorable one.

## Required boundaries

- Compare baseline and candidate on identical `(origin, target_date, horizon, unit)` keys and identical actual values.
- Treat candidate-minus-baseline WIS and MAE below zero as improvement.
- Keep candidate selection and tuning inside development data. Outcomes already inspected cannot become confirmation evidence later.
- A `promoted` label requires a matching protocol lock, explicit audit-gate confirmation, and no registered horizon or stratum warning. Feature and data-source candidates additionally require origin-level availability evidence; other kinds require hash-verified structured audit artifacts.
- Describe a rejection as applying to the tested candidate representation, not every possible use of its source, feature, or model family.
- Keep patient-level, identifiable, restricted, credential-bearing, or unclear-license artifacts out of public outputs. Aggregate predictions are not automatically public-safe; inspect their disclosure risk.
- Treat the evidence card as conditional on the supplied provenance. It is not a causal, clinical, or deployment-safety claim.

## Deliverable

Return the candidate ID and kind, registration and verification status, decision state, paired WIS and MAE differences, origin-bootstrap interval, proportion of improved origins, coverage change, horizon or registered-stratum warnings, failed or missing audit checks, and the paths to generated evidence. Lead with invalidity or missing provenance before discussing favorable metrics.
