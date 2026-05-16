from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional


class ScoringMode(str, Enum):
    PENALTY = "penalty"
    NO_PENALTY = "no_penalty"


class StartUnitType(str, Enum):
    INDIVIDUAL = "individual"
    PAIR = "pair"
    GROUP = "group"


class ResultStatus(str, Enum):
    OK = "ok"
    NOT_FINISHED = "not_finished"
    STAGE_DQ = "stage_dq"
    DISTANCE_DQ = "distance_dq"
    OVER_TIME_LIMIT = "over_time_limit"
    OUT_OF_COMPETITION = "out_of_competition"

    @property
    def protocol_label(self) -> str:
        return {
            ResultStatus.OK: "",
            ResultStatus.NOT_FINISHED: "не фин.",
            ResultStatus.STAGE_DQ: "сн с этапов",
            ResultStatus.DISTANCE_DQ: "сн с дист",
            ResultStatus.OVER_TIME_LIMIT: "прев. КВ",
            ResultStatus.OUT_OF_COMPETITION: "в/к",
        }[self]


@dataclass
class TourismSettings:
    scoring_mode: ScoringMode = ScoringMode.PENALTY
    penalty_unit_seconds: int = 30
    control_time_seconds: Optional[int] = None
    auto_over_time_limit: bool = True
    stage_dq_gets_place: bool = False
    show_zero_point_teams: bool = True
    zero_point_teams_get_place: bool = False
    team_best_count: int = 4
    group_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class StageResult:
    number: int
    name: str = ""
    penalty_points: int = 0
    cutoff_seconds: int = 0
    is_stage_dq: bool = False
    si_miss: bool = False
    comment: str = ""


@dataclass
class TourismResult:
    identifier: str
    name: str
    team: str = ""
    region: str = ""
    group: str = ""
    unit_type: StartUnitType = StartUnitType.INDIVIDUAL
    start_seconds: Optional[int] = None
    finish_seconds: Optional[int] = None
    stages: List[StageResult] = field(default_factory=list)
    status: ResultStatus = ResultStatus.OK
    place: Optional[int] = None
    points: int = 0

    pure_time_seconds: Optional[int] = None
    cutoff_sum_seconds: int = 0
    penalty_points_sum: int = 0
    penalty_time_seconds: int = 0
    stage_dq_count: int = 0
    si_miss_count: int = 0
    final_time_seconds: Optional[int] = None

    @property
    def team_group(self) -> str:
        return self.group

    def has_valid_time(self) -> bool:
        return self.start_seconds is not None and self.finish_seconds is not None


def sum_stage_values(stages: Iterable[StageResult]) -> tuple[int, int, int, int]:
    penalty_points = 0
    cutoff_seconds = 0
    stage_dq_count = 0
    si_miss_count = 0
    for stage in stages:
        penalty_points += max(0, int(stage.penalty_points or 0))
        cutoff_seconds += max(0, int(stage.cutoff_seconds or 0))
        stage_dq_count += 1 if stage.is_stage_dq else 0
        si_miss_count += 1 if stage.si_miss else 0
    return penalty_points, cutoff_seconds, stage_dq_count, si_miss_count
