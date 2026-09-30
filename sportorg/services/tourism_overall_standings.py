from dataclasses import dataclass
from typing import Dict, List

from sportorg.models.memory import race
from sportorg.services.tourism_scores import (
    calculate_tourism_team_places_and_scores,
    get_score_by_place,
    get_tourism_scores_array,
)


TOURISM_TEAM_TYPES = {
    'tourism_pair',
    'tourism_group',
}


@dataclass
class TourismStandingRow:
    place: str
    group_name: str
    team_name: str
    scores: int
    unit_count: int
    details: str


@dataclass
class TourismTeamScoreItem:
    scores: int
    detail: str
    is_female: bool = False


def _team_name_from_person(person) -> str:
    if person and person.organization:
        return person.organization.name
    return 'Без коллектива'


def _source_group_name_from_person(person) -> str:
    if person and person.group:
        return person.group.name
    return 'Без группы'


def _combined_age_group_name(group_name: str) -> str:
    """Объединяет женские и мужские группы в одну зачётную возрастную категорию.

    Примеры:
    Ж-KINDER -> KINDER
    М-KINDER -> KINDER
    Ж-МАЛ-ДЕВ -> МАЛ-ДЕВ
    М-МАЛ-ДЕВ -> МАЛ-ДЕВ
    Ж-ЮН-ДЕВ (14-15 ЛЕТ) -> ЮН-ДЕВ (14-15 ЛЕТ)
    М-ЮН-ДЕВ (14-15 ЛЕТ) -> ЮН-ДЕВ (14-15 ЛЕТ)
    """
    group_name = str(group_name or '').strip()

    if not group_name:
        return 'Без группы'

    normalized = group_name.replace('—', '-').replace('–', '-').strip()
    upper = normalized.upper()

    for prefix in ('Ж-', 'М-'):
        if upper.startswith(prefix):
            return normalized[2:].strip() or group_name

    # Запасной вариант для записей вида "Ж KINDER" или "М KINDER".
    if len(normalized) > 2 and upper[0] in ('Ж', 'М') and normalized[1].isspace():
        return normalized[2:].strip() or group_name

    return group_name


def _is_female_group_name(group_name: str, female_prefix: str) -> bool:
    group_name = str(group_name or '').strip().upper()
    female_prefix = str(female_prefix or 'Ж').strip().upper()

    if not female_prefix:
        female_prefix = 'Ж'

    return group_name.startswith(female_prefix)


def _result_place_key(result, obj):
    result_time = result.get_result_otime().to_msec()
    stage_dsq_count = int(
        getattr(result, 'tourism_stage_dsq_count', 0) or 0
    )

    if obj.get_setting('result_processing_mode', 'time') == 'scores':
        # В рогейне личный протокол ранжирует сначала по убыванию баллов,
        # а при равенстве баллов — по возрастанию времени.
        return (
            stage_dsq_count,
            -int(getattr(result, 'rogaine_score', 0) or 0),
            result_time,
        )

    return (stage_dsq_count, result_time)


def _sort_result_key(result, obj):
    if not result or not result.is_status_ok():
        return (1, 999999999999, 999999999999)

    result_time = result.get_result_otime().to_msec()
    if result_time <= 0:
        return (1, 999999999999, 999999999999)

    return (0,) + _result_place_key(result, obj)


def _get_standings_settings(obj):
    count_scores = int(obj.get_setting('tourism_standings_count_scores', 0) or 0)
    min_female_count = int(
        obj.get_setting('tourism_standings_min_female_count', 0) or 0
    )
    female_prefix = str(
        obj.get_setting('tourism_standings_female_group_prefix', 'Ж') or 'Ж'
    )

    if count_scores < 0:
        count_scores = 0

    if min_female_count < 0:
        min_female_count = 0

    if count_scores > 0 and min_female_count > count_scores:
        min_female_count = count_scores

    return count_scores, min_female_count, female_prefix


def get_tourism_standings_rules(obj=None):
    obj = obj or race()
    count_scores, min_female_count, female_prefix = _get_standings_settings(obj)
    return {
        'count_scores': count_scores,
        'min_female_count': min_female_count,
        'female_prefix': female_prefix,
    }


def _apply_team_score_rules(
    items: List[TourismTeamScoreItem],
    count_scores: int,
    min_female_count: int,
):
    # Если количество зачётных результатов = 0, берём все результаты.
    if count_scores <= 0:
        return sorted(items, key=lambda item: item.scores, reverse=True)

    if min_female_count <= 0:
        return sorted(items, key=lambda item: item.scores, reverse=True)[:count_scores]

    # Места, зарезервированные под женские результаты, нельзя
    # заполнять мужскими. Если женщин меньше минимума, команда
    # получает меньше зачётных результатов. Например: 4 в зачёт,
    # минимум 2 женщины, в команде 3 мужчины + 1 женщина => 3 результата.
    sorted_items = sorted(items, key=lambda item: item.scores, reverse=True)
    max_non_female_count = max(0, count_scores - min_female_count)
    selected = []
    selected_non_female_count = 0

    for item in sorted_items:
        if len(selected) >= count_scores:
            break
        if item.is_female:
            selected.append(item)
        elif selected_non_female_count < max_non_female_count:
            selected.append(item)
            selected_non_female_count += 1

    return selected


def _standing_rows_for_group(
    group_name: str,
    team_items: Dict[str, List[TourismTeamScoreItem]],
    obj,
) -> List[TourismStandingRow]:
    count_scores, min_female_count, _female_prefix = _get_standings_settings(obj)

    raw_rows = []

    for team_name, items in team_items.items():
        counted_items = _apply_team_score_rules(
            items,
            count_scores=count_scores,
            min_female_count=min_female_count,
        )

        total_scores = sum(item.scores for item in counted_items)
        details = '; '.join(item.detail for item in counted_items)

        raw_rows.append(
            TourismStandingRow(
                place='',
                group_name=group_name,
                team_name=team_name,
                scores=int(total_scores or 0),
                unit_count=len(counted_items),
                details=details,
            )
        )

    raw_rows.sort(key=lambda row: (-row.scores, row.team_name.lower()))

    current_place = 0
    previous_scores = None

    for index, row in enumerate(raw_rows, 1):
        if previous_scores is None or row.scores != previous_scores:
            current_place = index
            previous_scores = row.scores

        # Команды с нулевыми очками место не получают.
        row.place = current_place if row.scores > 0 else ''

    return raw_rows


def _build_individual_standings(obj):
    scores_array = get_tourism_scores_array(obj)
    _count_scores, _min_female_count, female_prefix = _get_standings_settings(obj)

    # ВАЖНО:
    # Командный зачёт считается по объединённой возрастной категории:
    # Ж-KINDER + М-KINDER = KINDER.
    # Но личные места для начисления очков считаются внутри исходных групп Ж/М.
    grouped_results_by_source_group = {}

    for result in getattr(obj, 'results', []):
        person = getattr(result, 'person', None)
        if not person:
            continue

        source_group_name = _source_group_name_from_person(person)
        grouped_results_by_source_group.setdefault(source_group_name, []).append(result)

    # team_items_by_combined_group:
    # {
    #   'KINDER': {
    #       'Команда 1': [очки из Ж-KINDER и М-KINDER],
    #   }
    # }
    team_items_by_combined_group: Dict[str, Dict[str, List[TourismTeamScoreItem]]] = {}

    for source_group_name in sorted(grouped_results_by_source_group.keys(), key=lambda x: x.lower()):
        results = sorted(
            grouped_results_by_source_group[source_group_name],
            key=lambda result: _sort_result_key(result, obj),
        )

        combined_group_name = _combined_age_group_name(source_group_name)
        is_female = _is_female_group_name(source_group_name, female_prefix)

        current_place = 0
        previous_place_key = None
        counted = 0

        for result in results:
            if not result.is_status_ok():
                continue

            result_time = result.get_result_otime().to_msec()
            if result_time <= 0:
                continue

            counted += 1

            place_key = _result_place_key(result, obj)
            if previous_place_key is None or place_key != previous_place_key:
                current_place = counted
                previous_place_key = place_key

            scores = get_score_by_place(scores_array, current_place)
            team_name = _team_name_from_person(result.person)

            detail = (
                f'{result.person.full_name} [{source_group_name}]: '
                f'{current_place} место, {scores} очк.'
            )

            team_items_by_combined_group.setdefault(combined_group_name, {})
            team_items_by_combined_group[combined_group_name].setdefault(team_name, [])
            team_items_by_combined_group[combined_group_name][team_name].append(
                TourismTeamScoreItem(
                    scores=scores,
                    detail=detail,
                    is_female=is_female,
                )
            )

    all_rows: List[TourismStandingRow] = []

    for combined_group_name in sorted(team_items_by_combined_group.keys(), key=lambda x: x.lower()):
        all_rows.extend(
            _standing_rows_for_group(
                combined_group_name,
                team_items_by_combined_group[combined_group_name],
                obj,
            )
        )

    return all_rows


def _build_team_unit_standings(obj):
    _count_scores, _min_female_count, female_prefix = _get_standings_settings(obj)
    units = calculate_tourism_team_places_and_scores(obj)

    grouped_team_items: Dict[str, Dict[str, List[TourismTeamScoreItem]]] = {}

    for unit in units:
        scores = int(getattr(unit, 'tourism_scores', 0) or 0)
        source_group_name = unit.group_name or 'Без группы'
        combined_group_name = _combined_age_group_name(source_group_name)
        team_name = unit.team_name or 'Без коллектива'
        is_female = _is_female_group_name(source_group_name, female_prefix)

        place = getattr(unit, 'place', '')
        place_text = f'{place} место' if place else 'без места'
        detail = (
            f'№{unit.number} [{source_group_name}]: '
            f'{place_text}, {scores} очк. ({unit.members_text})'
        )

        grouped_team_items.setdefault(combined_group_name, {})
        grouped_team_items[combined_group_name].setdefault(team_name, [])
        grouped_team_items[combined_group_name][team_name].append(
            TourismTeamScoreItem(
                scores=scores,
                detail=detail,
                is_female=is_female,
            )
        )

    all_rows: List[TourismStandingRow] = []

    for combined_group_name in sorted(grouped_team_items.keys(), key=lambda x: x.lower()):
        all_rows.extend(
            _standing_rows_for_group(
                combined_group_name,
                grouped_team_items[combined_group_name],
                obj,
            )
        )

    return all_rows


def build_tourism_overall_standings(obj=None) -> List[TourismStandingRow]:
    obj = obj or race()
    competition_type = getattr(obj, 'competition_type', '')

    if competition_type in TOURISM_TEAM_TYPES:
        return _build_team_unit_standings(obj)

    return _build_individual_standings(obj)


def _build_individual_territorial_standings(obj):
    scores_array = get_tourism_scores_array(obj)
    _count_scores, _min_female_count, female_prefix = _get_standings_settings(obj)
    grouped_results = {}

    for result in getattr(obj, 'results', []):
        person = getattr(result, 'person', None)
        if person:
            source_group = _source_group_name_from_person(person)
            grouped_results.setdefault(source_group, []).append(result)

    team_items: Dict[str, List[TourismTeamScoreItem]] = {}
    for source_group in sorted(grouped_results, key=lambda value: value.lower()):
        results = sorted(
            grouped_results[source_group],
            key=lambda result: _sort_result_key(result, obj),
        )
        is_female = _is_female_group_name(source_group, female_prefix)
        current_place = 0
        previous_place_key = None
        counted = 0

        for result in results:
            if not result.is_status_ok():
                continue
            result_time = result.get_result_otime().to_msec()
            if result_time <= 0:
                continue
            counted += 1
            place_key = _result_place_key(result, obj)
            if previous_place_key is None or place_key != previous_place_key:
                current_place = counted
                previous_place_key = place_key
            scores = get_score_by_place(scores_array, current_place)
            team_name = _team_name_from_person(result.person)
            detail = (
                f'{result.person.full_name} [{source_group}]: '
                f'{current_place} место, {scores} очк.'
            )
            team_items.setdefault(team_name, []).append(
                TourismTeamScoreItem(scores=scores, detail=detail, is_female=is_female)
            )

    return _standing_rows_for_group('Все возрастные категории', team_items, obj)


def _build_team_unit_territorial_standings(obj):
    _count_scores, _min_female_count, female_prefix = _get_standings_settings(obj)
    team_items: Dict[str, List[TourismTeamScoreItem]] = {}

    for unit in calculate_tourism_team_places_and_scores(obj):
        source_group = unit.group_name or 'Без группы'
        team_name = unit.team_name or 'Без коллектива'
        scores = int(getattr(unit, 'tourism_scores', 0) or 0)
        place = getattr(unit, 'place', '')
        place_text = f'{place} место' if place else 'без места'
        detail = (
            f'№{unit.number} [{source_group}]: {place_text}, '
            f'{scores} очк. ({unit.members_text})'
        )
        team_items.setdefault(team_name, []).append(
            TourismTeamScoreItem(
                scores=scores,
                detail=detail,
                is_female=_is_female_group_name(source_group, female_prefix),
            )
        )

    return _standing_rows_for_group('Все возрастные категории', team_items, obj)


def build_tourism_territorial_standings(obj=None) -> List[TourismStandingRow]:
    """Overall collective standings across every age category."""
    obj = obj or race()
    if getattr(obj, 'competition_type', '') in TOURISM_TEAM_TYPES:
        return _build_team_unit_territorial_standings(obj)
    return _build_individual_territorial_standings(obj)
