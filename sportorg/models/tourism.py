from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CompetitionType(str, Enum):
    INDIVIDUAL = "individual"
    RELAY = "relay"
    TOURISM = "tourism"


class TourismJudgingMode(str, Enum):
    PENALTY = "penalty"
    NO_PENALTY = "no_penalty"


@dataclass
class TourismCourse:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    group_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.__class__.__name__,
            "id": self.id,
            "name": self.name,
            "group_ids": list(self.group_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TourismCourse":
        return cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            name=str(data.get("name", "")),
            group_ids=[str(x) for x in data.get("group_ids", [])],
        )


@dataclass
class TourismStage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tourism_course_id: str = ""
    order_num: int = 0
    name: str = ""

    # совместимость со старой схемой, где этап был привязан к group_id
    group_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.__class__.__name__,
            "id": self.id,
            "tourism_course_id": self.tourism_course_id,
            "group_id": self.group_id,
            "order_num": self.order_num,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TourismStage":
        return cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            tourism_course_id=str(data.get("tourism_course_id", "")),
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


def find_tourism_course_for_group(obj: Any, group_id: str) -> Optional[TourismCourse]:
    ensure_tourism_defaults(obj)
    group_id = str(group_id)

    for course in obj.tourism_courses:
        if group_id in [str(x) for x in getattr(course, "group_ids", [])]:
            return course

    return None


def get_tourism_stages_for_group(obj: Any, group_id: str):
    """
    Возвращает этапы для группы.

    Основная схема:
    group_id -> tourism_course.group_ids -> tourism_stages.tourism_course_id

    Резервные схемы нужны потому, что в ходе доработок могли сохраниться данные:
    - этапы напрямую по stage.group_id;
    - этапы по tourism_course_id, но group_ids ещё не записались;
    - одна туристская дистанция есть, этапы есть, но связь с группой потеряна.
    """
    normalize_tourism_links(obj)
    group_id = str(group_id)

    all_stages = list(getattr(obj, "tourism_stages", []) or [])
    all_courses = list(getattr(obj, "tourism_courses", []) or [])

    # 1. Основная схема: группа отмечена чекбоксом у туристской дистанции.
    course = get_tourism_course_for_group(obj, group_id)
    if course:
        course_id = str(course.id)
        stages = [
            stage for stage in all_stages
            if str(getattr(stage, "tourism_course_id", "") or "") == course_id
        ]
        if stages:
            return sorted(stages, key=lambda x: int(getattr(x, "order_num", 0) or 0))

    # 2. Старая схема: этапы были привязаны напрямую к группе.
    stages = [
        stage for stage in all_stages
        if str(getattr(stage, "group_id", "") or "") == group_id
    ]
    if stages:
        return sorted(stages, key=lambda x: int(getattr(x, "order_num", 0) or 0))

    # 3. Резерв: если есть ровно одна туристская дистанция с этапами,
    # показываем её этапы. Это удобно для типового случая:
    # одна дистанция + несколько групп.
    course_ids_with_stages = []
    for course in all_courses:
        course_id = str(course.id)
        stages_for_course = [
            stage for stage in all_stages
            if str(getattr(stage, "tourism_course_id", "") or "") == course_id
        ]
        if stages_for_course:
            course_ids_with_stages.append((course_id, stages_for_course))

    if len(course_ids_with_stages) == 1:
        return sorted(
            course_ids_with_stages[0][1],
            key=lambda x: int(getattr(x, "order_num", 0) or 0)
        )

    # 4. Последний резерв: если туристских дистанций нет или они пустые,
    # но этапы вообще есть, показываем все этапы.
    # Это помогает не потерять этапы, созданные ранними версиями патча.
    if all_stages and not all_courses:
        return sorted(all_stages, key=lambda x: int(getattr(x, "order_num", 0) or 0))

    return []

def ensure_tourism_defaults(obj: Any) -> None:
    if not hasattr(obj, "competition_type"):
        obj.competition_type = CompetitionType.INDIVIDUAL.value

    if not hasattr(obj, "tourism_judging_mode"):
        obj.tourism_judging_mode = TourismJudgingMode.PENALTY.value

    if not hasattr(obj, "tourism_courses"):
        obj.tourism_courses: List[TourismCourse] = []

    if not hasattr(obj, "tourism_stages"):
        obj.tourism_stages: List[TourismStage] = []

    if not hasattr(obj, "tourism_stage_decisions"):
        obj.tourism_stage_decisions: List[TourismStageDecision] = []

    # Миграция старой схемы: если есть этапы с group_id, но нет дистанций,
    # создаём отдельные дистанции по группам, чтобы старые данные не потерялись.
    if not obj.tourism_courses and obj.tourism_stages:
        grouped = {}
        for stage in obj.tourism_stages:
            old_group_id = str(getattr(stage, "group_id", "") or "")
            if not old_group_id:
                continue

            if old_group_id not in grouped:
                course = TourismCourse(
                    name=f"Дистанция группы {old_group_id}",
                    group_ids=[old_group_id],
                )
                grouped[old_group_id] = course
                obj.tourism_courses.append(course)

            stage.tourism_course_id = grouped[old_group_id].id



def get_tourism_course_for_group(obj: Any, group_id: str):
    """Return tourism course assigned to the group.

    New schema:
    - TourismCourse.group_ids contains one or more group IDs.
    - TourismStage.tourism_course_id points to TourismCourse.id.

    Backward compatibility:
    - old TourismStage.group_id is still accepted.
    """
    ensure_tourism_defaults(obj)
    group_id = str(group_id)

    for course in getattr(obj, "tourism_courses", []):
        if group_id in [str(x) for x in getattr(course, "group_ids", [])]:
            return course

    return None


def get_tourism_stages_for_group(obj: Any, group_id: str):
    ensure_tourism_defaults(obj)
    group_id = str(group_id)

    course = get_tourism_course_for_group(obj, group_id)
    if course:
        stages = [
            x for x in getattr(obj, "tourism_stages", [])
            if str(getattr(x, "tourism_course_id", "")) == str(course.id)
        ]
        return sorted(stages, key=lambda x: x.order_num)

    # Old schema fallback.
    stages = [
        x for x in getattr(obj, "tourism_stages", [])
        if str(getattr(x, "group_id", "")) == group_id
    ]
    return sorted(stages, key=lambda x: x.order_num)


def get_stage_name(obj: Any, stage_id: str) -> str:
    ensure_tourism_defaults(obj)
    for stage in getattr(obj, "tourism_stages", []):
        if str(stage.id) == str(stage_id):
            return stage.name
    return ""


# --- tourism group/course/stage link helpers ---

def normalize_tourism_links(obj: Any) -> None:
    """
    Приводит связи туризма к единому виду:
    - у каждой туристской дистанции group_ids хранятся строками;
    - этапы ищутся через tourism_course_id;
    - старая схема stage.group_id сохраняется как резервная.
    """
    ensure_tourism_defaults(obj)

    for course in getattr(obj, "tourism_courses", []):
        course.group_ids = [str(x) for x in getattr(course, "group_ids", []) if str(x)]

    for stage in getattr(obj, "tourism_stages", []):
        if hasattr(stage, "tourism_course_id"):
            stage.tourism_course_id = str(getattr(stage, "tourism_course_id", "") or "")
        if hasattr(stage, "group_id"):
            stage.group_id = str(getattr(stage, "group_id", "") or "")


def get_tourism_course_for_group(obj: Any, group_id: str):
    """
    Возвращает туристскую дистанцию, к которой привязана группа.
    """
    normalize_tourism_links(obj)
    group_id = str(group_id)

    for course in getattr(obj, "tourism_courses", []):
        if group_id in [str(x) for x in getattr(course, "group_ids", [])]:
            return course

    return None


def get_tourism_stages_for_group(obj: Any, group_id: str):
    """
    Возвращает этапы для группы:
    1) основная схема: group -> tourism_course.group_ids -> stages.tourism_course_id;
    2) резервная старая схема: stages.group_id.
    """
    normalize_tourism_links(obj)
    group_id = str(group_id)

    course = get_tourism_course_for_group(obj, group_id)
    stages = []

    if course:
        course_id = str(course.id)
        stages = [
            x for x in getattr(obj, "tourism_stages", [])
            if str(getattr(x, "tourism_course_id", "")) == course_id
        ]

    # Резерв для старых данных, если этапы ещё записаны напрямую на группу.
    if not stages:
        stages = [
            x for x in getattr(obj, "tourism_stages", [])
            if str(getattr(x, "group_id", "")) == group_id
        ]

    return sorted(stages, key=lambda x: int(getattr(x, "order_num", 0) or 0))

