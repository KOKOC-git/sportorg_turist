from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class CompetitionType(str, Enum):
    INDIVIDUAL = "individual"
    RELAY = "relay"
    TOURISM = "tourism"


class TourismJudgingMode(str, Enum):
    PENALTY = "penalty"
    NO_PENALTY = "no_penalty"


@dataclass
class TourismStage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str = ""
    order_num: int = 0
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.__class__.__name__,
            "id": self.id,
            "group_id": self.group_id,
            "order_num": self.order_num,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TourismStage":
        return cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            group_id=str(data.get("group_id", "")),
            order_num=int(data.get("order_num", 0)),
            name=str(data.get("name", "")),
        )


@dataclass
class TourismStageDecision:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage_id: str = ""
    person_id: str = ""
    penalty_time_sec: int = 0
    penalty_points: int = 0
    cutoff_time_sec: int = 0
    is_stage_dsq: bool = False
    comment: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def validate(self, judging_mode: TourismJudgingMode) -> None:
        if self.is_stage_dsq:
            self.penalty_time_sec = 0
            self.penalty_points = 0

        if judging_mode == TourismJudgingMode.NO_PENALTY:
            self.penalty_time_sec = 0
            self.penalty_points = 0

        if self.penalty_time_sec and self.penalty_points:
            raise ValueError("Нельзя одновременно задать штраф временем и штраф баллами")

        if (
            not self.is_stage_dsq
            and self.penalty_time_sec == 0
            and self.penalty_points == 0
            and self.cutoff_time_sec == 0
        ):
            raise ValueError("Не задана ни одна санкция")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.__class__.__name__,
            "id": self.id,
            "stage_id": self.stage_id,
            "person_id": self.person_id,
            "penalty_time_sec": self.penalty_time_sec,
            "penalty_points": self.penalty_points,
            "cutoff_time_sec": self.cutoff_time_sec,
            "is_stage_dsq": self.is_stage_dsq,
            "comment": self.comment,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TourismStageDecision":
        return cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            stage_id=str(data.get("stage_id", "")),
            person_id=str(data.get("person_id", "")),
            penalty_time_sec=int(data.get("penalty_time_sec", 0)),
            penalty_points=int(data.get("penalty_points", 0)),
            cutoff_time_sec=int(data.get("cutoff_time_sec", 0)),
            is_stage_dsq=bool(data.get("is_stage_dsq", False)),
            comment=str(data.get("comment", "")),
            created_at=str(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=str(data.get("updated_at", datetime.utcnow().isoformat())),
        )


def sec_to_hms(value: int) -> str:
    value = max(0, int(value))
    h = value // 3600
    m = (value % 3600) // 60
    s = value % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def hms_to_sec(value: str) -> int:
    value = (value or "").strip()
    if not value:
        return 0

    parts = value.split(":")
    if len(parts) == 2:
        h = 0
        m, s = parts
    elif len(parts) == 3:
        h, m, s = parts
    else:
        raise ValueError("Ожидается формат HH:MM:SS или MM:SS")

    return int(h) * 3600 + int(m) * 60 + int(s)


def ensure_tourism_defaults(obj: Any) -> None:
    if not hasattr(obj, "competition_type"):
        obj.competition_type = CompetitionType.INDIVIDUAL.value

    if not hasattr(obj, "tourism_judging_mode"):
        obj.tourism_judging_mode = TourismJudgingMode.PENALTY.value

    if not hasattr(obj, "tourism_stages"):
        obj.tourism_stages: List[TourismStage] = []

    if not hasattr(obj, "tourism_stage_decisions"):
        obj.tourism_stage_decisions: List[TourismStageDecision] = []