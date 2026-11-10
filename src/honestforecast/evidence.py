"""Minimal human-readable evidence card generation."""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from .comparison import FamilyDecision
from .contracts import ForecastContract


def render_evidence_card(
    study_id: str,
    experiment_id: str,
    metrics: Mapping[str, float],
    scenario_results: Mapping[str, str],
) -> str:
    scenarios = "\n".join(
        f"- {scenario}: {result}" for scenario, result in sorted(scenario_results.items())
    )
    return f"""# Forecast evidence card

## Identity

- Study: `{study_id}`
- Experiment: `{experiment_id}`
- Decision state: `exploratory`
- Evidence level: `E4 synthetic known-answer execution`

## Evaluation grid

- Common scored cases: {int(metrics['n_cases'])}
- Horizons: 1 and 2 months

## Metrics regenerated from prediction rows

- MAE: {metrics['mae']:.6f}
- WIS: {metrics['wis']:.6f}
- 50% coverage: {metrics['coverage_50']:.3f}
- 80% coverage: {metrics['coverage_80']:.3f}
- 95% coverage: {metrics['coverage_95']:.3f}
- 95% mean interval width: {metrics['width_95']:.3f}

## Known-answer audit outcomes

{scenarios}

## Interpretation

This card verifies core mechanics on synthetic evidence. It does not establish public-health forecast skill or a clinical claim.
"""


def render_assessment_evidence_card(
    *,
    contract: ForecastContract,
    candidate_id: str,
    candidate_kind: str,
    registered_items: Sequence[str],
    registered_strata: Sequence[str],
    n_units: int,
    baseline_metrics: Mapping[str, float],
    candidate_metrics: Mapping[str, float],
    decision: FamilyDecision,
    checks: Mapping[str, str],
    input_hashes: Mapping[str, str],
    registration_sha256: Optional[str] = None,
) -> str:
    """Render the portable evidence card emitted by ``honestforecast assess``."""
    warnings = (
        "\n".join(f"- `{warning}`" for warning in decision.warnings)
        if decision.warnings
        else "- None"
    )
    check_rows = "\n".join(
        f"| {name} | `{result}` |" for name, result in sorted(checks.items())
    )
    hash_rows = "\n".join(
        f"- {name}: `{digest}`" for name, digest in sorted(input_hashes.items())
    )
    items = (
        ", ".join(f"`{item}`" for item in registered_items)
        or "None supplied by this schema"
    )
    interpretation = {
        "promoted": "The candidate passed the supplied confirmation and audit claims plus the registered robustness gate.",
        "challenger": "The candidate is promising, but the evidence is not sufficient for promotion.",
        "rejected": "The candidate did not improve WIS under this registered representation.",
    }[decision.state]
    return f"""# Forecast change evidence card

## Identity

- Study: `{contract.study_id}`
- Candidate: `{candidate_id}`
- Candidate kind: `{candidate_kind}`
- Registered evidence items: {items}
- Protocol registration: `{checks.get('protocol_registration', 'not_provided')}`
- Registration digest: `{registration_sha256 or 'None'}`
- Decision state: `{decision.state}`
- Evidence level: `E3 report regeneration`

## Evaluation grid

- Common scored cases: {decision.n_cases}
- Forecast origins: {decision.n_origins}
- Forecast units: {n_units}
- Horizons: {", ".join(str(value) for value in contract.horizons)}
- Registered strata: {", ".join(registered_strata) or "None"}

## Metrics regenerated from prediction rows

| Method | MAE | WIS | 80% coverage | 80% width |
| --- | ---: | ---: | ---: | ---: |
| Baseline | {baseline_metrics['mae']:.6f} | {baseline_metrics['wis']:.6f} | {baseline_metrics['coverage_80']:.3f} | {baseline_metrics['width_80']:.3f} |
| Candidate | {candidate_metrics['mae']:.6f} | {candidate_metrics['wis']:.6f} | {candidate_metrics['coverage_80']:.3f} | {candidate_metrics['width_80']:.3f} |

Differences use candidate minus baseline, so negative errors favor the candidate.

- Mean paired WIS difference: {decision.mean_wis_difference:.6f}
- Mean paired MAE difference: {decision.mean_mae_difference:.6f}
- Origins improved: {decision.improved_origin_proportion:.3f}
- Origin-bootstrap 95% interval: [{decision.bootstrap_95_lower:.6f}, {decision.bootstrap_95_upper:.6f}]
- Drop-best-origin WIS difference: {decision.drop_best_origin_wis_difference:.6f}

## Robustness warnings

{warnings}

## Audit checks

| Check | Result |
| --- | --- |
{check_rows}

## Input hashes

{hash_rows}

## Interpretation

{interpretation}

The tool validates the supplied artifacts and protocol lock, not the truth of upstream provenance or the lock's local timestamp. External time evidence such as a public Git commit or registry is still required for a strong preregistration claim. A `promoted` result is not a causal, clinical, or operational-safety claim.
"""
