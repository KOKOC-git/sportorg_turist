from __future__ import annotations

import re

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CompetitionType(str, Enum):
    INDIVIDUAL = "individual"
    RELAY = "relay"
    TOURISM = "tourism"


TOURISM_COMPETITION_TYPES = {
    CompetitionType.TOURISM.value,
    'tourism_individual',
    'tourism_pair',
    'tourism_group',
}


def is_tourism_competition_type(value: Any) -> bool:
    return value in TOURISM_COMPETITION_TYPES


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

    # Поддержка полей с маской ввода вида "__:__:__".
    # Если пользователь ничего не ввёл, считаем значение нулевым.
    if not value or value.replace(":", "").replace("_", "").strip() == "":
        return 0

    value = value.replace("_", "0")

    parts = value.split(":")
    if len(parts) == 2:
        h = 0
        m, s = parts
    elif len(parts) == 3:
        h, m, s = parts
    else:
        raise ValueError("Ожидается формат HH:MM:SS или MM:SS")

    return int(h) * 3600 + int(m) * 60 + int(s)


def normalize_hms_input(value: str) -> str:
    """
    Нормализует ввод времени для штрафов/отсечек.

    Поддерживает:
    30       -> 00:00:30
    130      -> 00:01:30
    0130     -> 00:01:30
    10130    -> 01:01:30
    01:30    -> 00:01:30
    1:01:30  -> 01:01:30

    Лишние символы из QLineEdit/InputMask игнорируются.
    """
    value = str(value or "").strip()

    if not value:
        return "00:00:00"

    # Убираем всё, кроме цифр и двоеточий.
    value = re.sub(r"[^0-9:]", "", value)

    if not value:
        return "00:00:00"

    if ":" in value:
        parts = [p for p in value.split(":") if p != ""]

        if len(parts) == 1:
            h, m, s = 0, 0, int(parts[0] or 0)
        elif len(parts) == 2:
            h, m, s = 0, int(parts[0] or 0), int(parts[1] or 0)
        else:
            h, m, s = int(parts[-3] or 0), int(parts[-2] or 0), int(parts[-1] or 0)
    else:
        digits = re.sub(r"\D", "", value)

        if not digits:
            return "00:00:00"

        # Последние 2 цифры — секунды, предыдущие 2 — минуты, остальное — часы.
        s = int(digits[-2:]) if len(digits) >= 2 else int(digits)
        m = int(digits[-4:-2]) if len(digits) >= 4 else 0
        h = int(digits[:-4]) if len(digits) > 4 else 0

    # Перенос переполнения секунд/минут.
    if s >= 60:
        m += s // 60
        s = s % 60

    if m >= 60:
        h += m // 60
        m = m % 60

    return f"{h:02d}:{m:02d}:{s:02d}"



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



def repair_tourism_courses_from_stages(obj: Any) -> None:
    """
    Восстанавливает список туристских дистанций, если в старом/повреждённом файле
    есть tourism_stages с tourism_course_id, но нет tourism_courses.

    Это важно, чтобы:
    - ранее созданные этапы не пропадали из окна настройки этапов;
    - ранее назначенные штрафы продолжали ссылаться на настоящие этапы;
    - не создавались лишние "Восстановленные этапы".
    """
    ensure_tourism_defaults(obj)

    stages = list(getattr(obj, "tourism_stages", []) or [])
    decisions = list(getattr(obj, "tourism_stage_decisions", []) or [])
    courses = list(getattr(obj, "tourism_courses", []) or [])

    # Если дистанции уже есть — только дочистим group_ids.
    existing_course_ids = {
        str(getattr(course, "id", "") or "")
        for course in courses
        if str(getattr(course, "id", "") or "")
    }

    stage_course_ids = []
    for stage in stages:
        course_id = str(getattr(stage, "tourism_course_id", "") or "")
        if course_id and course_id not in stage_course_ids:
            stage_course_ids.append(course_id)

    if not stage_course_ids:
        return

    # Создаём отсутствующие дистанции под уже существующие course_id этапов.
    for course_id in stage_course_ids:
        if course_id not in existing_course_ids:
            course = TourismCourse(
                id=course_id,
                name=f"Туристская дистанция {len(obj.tourism_courses) + 1}",
                group_ids=[],
            )
            obj.tourism_courses.append(course)
            existing_course_ids.add(course_id)

    course_by_id = {
        str(getattr(course, "id", "") or ""): course
        for course in getattr(obj, "tourism_courses", [])
    }

    stage_by_id = {
        str(getattr(stage, "id", "") or ""): stage
        for stage in stages
    }

    person_by_id = {}
    for person in getattr(obj, "persons", []) or []:
        person_by_id[str(getattr(person, "id", "") or "")] = person

    # По уже существующим штрафам понимаем:
    # участник -> группа -> к какой дистанции привязан этап решения.
    for decision in decisions:
        stage = stage_by_id.get(str(getattr(decision, "stage_id", "") or ""))
        if not stage:
            continue

        course_id = str(getattr(stage, "tourism_course_id", "") or "")
        if not course_id:
            continue

        course = course_by_id.get(course_id)
        if not course:
            continue

        person = person_by_id.get(str(getattr(decision, "person_id", "") or ""))
        group = getattr(person, "group", None) if person else None
        group_id = str(getattr(group, "id", "") or "") if group else ""

        if group_id and group_id not in [str(x) for x in getattr(course, "group_ids", [])]:
            course.group_ids.append(group_id)

    # Старый вариант: если у этапа был group_id, тоже переносим его в дистанцию.
    for stage in stages:
        course_id = str(getattr(stage, "tourism_course_id", "") or "")
        old_group_id = str(getattr(stage, "group_id", "") or "")
        course = course_by_id.get(course_id)

        if course and old_group_id and old_group_id not in [str(x) for x in getattr(course, "group_ids", [])]:
            course.group_ids.append(old_group_id)



def _stage_key(stage: Any) -> tuple:
    """
    Ключ для сопоставления этапов при восстановлении старых файлов:
    сначала порядок, потом название.
    """
    order_num = int(getattr(stage, "order_num", 0) or 0)
    name = str(getattr(stage, "name", "") or "").strip().lower()
    return order_num, name


def _is_auto_restored_stage(stage: Any) -> bool:
    """
    Такие этапы могли быть автоматически созданы ранними версиями патча.
    Их можно удалять, если они не нужны для сохранения штрафов.
    """

    name = str(getattr(stage, "name", "") or "").strip()
    return re.fullmatch(r"(Этап|Stage)\s+\d+", name) is not None


def repair_tourism_data(obj: Any) -> None:
    """
    Автоматический ремонт туристских данных.

    Исправляет ситуацию старых версий:
    - появились лишние пустые туристские дистанции;
    - появились восстановленные этапы вида "Этап 5", "Этап 6";
    - штрафы остались привязаны к восстановленным дублям, а не к реальным этапам.
    """
    courses = list(getattr(obj, "tourism_courses", []) or [])
    stages = list(getattr(obj, "tourism_stages", []) or [])
    decisions = list(getattr(obj, "tourism_stage_decisions", []) or [])

    if not stages:
        return

    # Активные дистанции — только те, к которым привязаны группы.
    active_courses = [
        course for course in courses
        if list(getattr(course, "group_ids", []) or [])
    ]

    # Если активных дистанций нет, не рискуем удалять данные.
    if not active_courses:
        return

    active_course_ids = {str(course.id) for course in active_courses}

    # Удаляем пустые туристские дистанции без групп.
    obj.tourism_courses = active_courses

    # Оставляем этапы только активных дистанций.
    active_stages = [
        stage for stage in stages
        if str(getattr(stage, "tourism_course_id", "") or "") in active_course_ids
    ]

    stages_by_course = {}
    for stage in active_stages:
        course_id = str(getattr(stage, "tourism_course_id", "") or "")
        stages_by_course.setdefault(course_id, []).append(stage)

    repaired_stages = []

    for course in obj.tourism_courses:
        course_id = str(course.id)
        course_stages = stages_by_course.get(course_id, [])

        if not course_stages:
            continue

        course_stages = sorted(
            course_stages,
            key=lambda s: int(getattr(s, "order_num", 0) or 0)
        )

        real_stages = []
        auto_restored_stages = []

        for stage in course_stages:
            name = str(getattr(stage, "name", "") or "").strip()

            # Автоматически восстановленные этапы.
            # Именно они у тебя и появляются как лишние.
            if re.fullmatch(r"Этап\s+\d+", name):
                auto_restored_stages.append(stage)
            else:
                real_stages.append(stage)

        if real_stages and auto_restored_stages:
            # Переносим штрафы с "Этап 5/6/..." на реальные этапы по кругу:
            # Этап 5 -> первый реальный, Этап 6 -> второй реальный и т.д.
            for index, restored_stage in enumerate(auto_restored_stages):
                target_stage = real_stages[index % len(real_stages)]

                old_id = str(restored_stage.id)
                new_id = str(target_stage.id)

                for decision in decisions:
                    if str(getattr(decision, "stage_id", "")) == old_id:
                        decision.stage_id = new_id

            # После переноса восстановленные дубли удаляем.
            course_stages = real_stages

        # Нормализуем порядок.
        for index, stage in enumerate(course_stages, 1):
            stage.order_num = index
            stage.tourism_course_id = course_id
            stage.group_id = ""
            repaired_stages.append(stage)

    # Если есть штрафы на несуществующие этапы и не удалось перенести,
    # не теряем их: создаём резервный этап только для такого штрафа.
    valid_stage_ids = {str(stage.id) for stage in repaired_stages}

    for decision in decisions:
        stage_id = str(getattr(decision, "stage_id", "") or "")
        if stage_id and stage_id not in valid_stage_ids:
            course = obj.tourism_courses[0]
            fallback = TourismStage(
                id=stage_id,
                tourism_course_id=str(course.id),
                group_id="",
                order_num=len(repaired_stages) + 1,
                name=f"Этап {len(repaired_stages) + 1}",
            )
            repaired_stages.append(fallback)
            valid_stage_ids.add(stage_id)

    obj.tourism_stages = repaired_stages
    obj.tourism_stage_decisions = decisions


def ensure_tourism_defaults(obj: Any) -> None:
    if not hasattr(obj, "competition_type"):
        obj.competition_type = CompetitionType.INDIVIDUAL.value

    if not hasattr(obj, "tourism_judging_mode"):
        obj.tourism_judging_mode = TourismJudgingMode.PENALTY.value

    if not hasattr(obj, "tourism_penalty_point_sec"):
        obj.tourism_penalty_point_sec = 30

    if not hasattr(obj, "tourism_courses"):
        obj.tourism_courses: List[TourismCourse] = []

    if not hasattr(obj, "tourism_stages"):
        obj.tourism_stages: List[TourismStage] = []

    if not hasattr(obj, "tourism_stage_decisions"):
        obj.tourism_stage_decisions: List[TourismStageDecision] = []

    repair_tourism_data(obj)

    try:
        repair_orphan_tourism_stages(obj)
    except NameError:
        # Функция объявлена ниже в файле, при первом импорте это безопасный fallback.
        pass

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




def repair_orphan_tourism_stages(obj: Any) -> int:
    """
    Восстанавливает и привязывает этапы, по которым уже есть штрафы/отсечки,
    но которые не отображаются в настройке этапов или в назначении штрафов.

    Причина: штрафы хранят stage_id, а этап мог потерять связь с группой/дистанцией.
    """
    if not hasattr(obj, "tourism_courses"):
        obj.tourism_courses = []

    if not hasattr(obj, "tourism_stages"):
        obj.tourism_stages = []

    if not hasattr(obj, "tourism_stage_decisions"):
        obj.tourism_stage_decisions = []

    person_map = {
        str(getattr(person, "id", "")): person
        for person in getattr(obj, "persons", [])
    }

    stage_map = {
        str(getattr(stage, "id", "")): stage
        for stage in obj.tourism_stages
    }

    changed = 0

    def find_or_create_course_for_group(group):
        nonlocal changed

        group_id = str(getattr(group, "id", "") or "")
        group_name = str(getattr(group, "name", "") or "")

        if not group_id:
            return None

        for course in obj.tourism_courses:
            group_ids = [str(x) for x in getattr(course, "group_ids", [])]
            if group_id in group_ids:
                return course

        # Если дистанции для группы нет — создаём её,
        # чтобы этапы начали отображаться в "Настроить этапы туризма".
        course = TourismCourse(
            name=f"Дистанция {group_name or group_id}",
            group_ids=[group_id],
        )
        obj.tourism_courses.append(course)
        changed += 1
        return course

    max_order_by_course = {}
    for stage in obj.tourism_stages:
        course_id = str(getattr(stage, "tourism_course_id", "") or "")
        try:
            order_num = int(getattr(stage, "order_num", 0) or 0)
        except Exception:
            order_num = 0
        max_order_by_course[course_id] = max(max_order_by_course.get(course_id, 0), order_num)

    for decision in obj.tourism_stage_decisions:
        stage_id = str(getattr(decision, "stage_id", "") or "")
        person_id = str(getattr(decision, "person_id", "") or "")

        if not stage_id:
            continue

        person = person_map.get(person_id)
        group = getattr(person, "group", None) if person else None
        course = find_or_create_course_for_group(group) if group else None
        course_id = str(getattr(course, "id", "") or "") if course else ""

        stage = stage_map.get(stage_id)

        if stage is None:
            order_num = max_order_by_course.get(course_id, 0) + 1
            max_order_by_course[course_id] = order_num

            stage = TourismStage(
                id=stage_id,
                order_num=order_num,
                name=f"Этап {order_num}",
            )
            obj.tourism_stages.append(stage)
            stage_map[stage_id] = stage
            changed += 1

        # Новая схема: этап принадлежит туристской дистанции.
        if hasattr(stage, "tourism_course_id") and course_id:
            if str(getattr(stage, "tourism_course_id", "") or "") != course_id:
                stage.tourism_course_id = course_id
                changed += 1

        # Старая схема: этап был привязан напрямую к группе.
        if hasattr(stage, "group_id") and group:
            group_id = str(getattr(group, "id", "") or "")
            if str(getattr(stage, "group_id", "") or "") != group_id:
                stage.group_id = group_id
                changed += 1

    return changed
