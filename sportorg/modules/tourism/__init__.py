"""Tourism competition support for SportOrg.

This package contains calculation, ranking and team scoring helpers for
sports tourism events: penalties, cut-offs, stage removals and team points.
The code is intentionally independent from GUI classes so it can be integrated
step-by-step into the existing SportOrg data model.
"""

from .models import (
    ResultStatus,
    ScoringMode,
    StartUnitType,
    StageResult,
    TourismResult,
    TourismSettings,
)
from .calculation import calculate_tourism_result
from .ranking import rank_tourism_results
from .team_score import calculate_team_scores

__all__ = [
    "ResultStatus",
    "ScoringMode",
    "StartUnitType",
    "StageResult",
    "TourismResult",
    "TourismSettings",
    "calculate_tourism_result",
    "rank_tourism_results",
    "calculate_team_scores",
]
