"""Audit-friendly forecasting research primitives."""

from .assessment import AssessmentError, assess
from .audit import (
    AuditError,
    assert_common_grid,
    assert_no_future_availability,
    assert_no_future_vintage,
)
from .comparison import (
    CandidateDecision,
    FamilyDecision,
    append_decision,
    compare_candidate,
    compare_feature_family,
)
from .contracts import ContractError, FeatureSpec, ForecastContract, load_feature_manifest
from .features import FeatureError, FeatureLineage, as_of_join, fit_fold_transform
from .metrics import MetricError, summarize_predictions, validate_prediction_rows
from .registration import (
    RegistrationError,
    load_registration,
    register_protocol,
    verify_assessment,
)
from .screening import ScreeningError, screen_candidates
from .vintages import GitSnapshot, SnapshotAudit, VintageError, audit_snapshots

__all__ = [
    "AssessmentError",
    "AuditError",
    "CandidateDecision",
    "ContractError",
    "FeatureSpec",
    "FeatureError",
    "FeatureLineage",
    "FamilyDecision",
    "ForecastContract",
    "GitSnapshot",
    "MetricError",
    "RegistrationError",
    "ScreeningError",
    "SnapshotAudit",
    "VintageError",
    "append_decision",
    "assess",
    "as_of_join",
    "assert_common_grid",
    "assert_no_future_availability",
    "assert_no_future_vintage",
    "audit_snapshots",
    "compare_feature_family",
    "compare_candidate",
    "fit_fold_transform",
    "load_feature_manifest",
    "load_registration",
    "register_protocol",
    "summarize_predictions",
    "validate_prediction_rows",
    "verify_assessment",
    "screen_candidates",
]

__version__ = "0.8.0"
