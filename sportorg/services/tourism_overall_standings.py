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


def _group_name_from_person(person) -> str:
    if person and person.group:
        return person.group.name
    return ''


def _is_female_group_name(group_name: str, female_prefix: str) -> bool:
    group_name = str(group_name or '').strip().upper()
    female_prefix = str(female_prefix or 'Ж').strip().upper()

    if not female_prefix:
        female_prefix = 'Ж'

    return group_name.startswith(female_prefix)


def _sort_result_key(result):
    if not result or not result.is_status_ok():
        return (1, 999999999999)

    result_time = result.get_result_otime().to_msec()
    if result_time <= 0:
        return (1, 999999999999)

    return (0, result_time)


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


def _apply_team_score_rules(
    items: List[TourismTeamScoreItem],
    count_scores: int,
    min_female_count: int,
):
    # Если количество зачётных результатов = 0, берём все результаты.
    if count_scores <= 0:
        return sorted(items, key=lambda item: item.scores, reverse=True)

    items = sorted(items, key=lambda item: item.scores, reverse=True)

    selected = items[:count_scores]
    rest = items[count_scores:]

    if min_female_count <= 0:
        return selected

    female_selected = [item for item in selected if item.is_female]
    need_female = min_female_count - len(female_selected)

    if need_female <= 0:
        return selected

    female_rest = [item for item in rest if item.is_female]
    if not female_rest:
        # Женских результатов не хватает физически — считаем по доступным данным.
        return selected

    # Заменяем самые слабые неженские результаты в выбранной части
    # на лучшие женские результаты из оставшихся.
    selected_non_female = [item for item in selected if not item.is_female]
    selected_non_female = sorted(selected_non_female, key=lambda item: item.scores)

    replacements = min(need_female, len(female_rest), len(selected_non_female))

    for index in range(replacements):
        remove_item = selected_non_female[index]
        add_item = female_rest[index]

        selected.remove(remove_item)
        selected.append(add_item)

    return sorted(selected, key=lambda item: item.scores, reverse=True)


def _standing_rows(team_items: Dict[str, List[TourismTeamScoreItem]], obj) -> List[TourismStandingRow]:
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

        row.place = current_place if row.scores > 0 else ''

    return raw_rows


def _build_individual_standings(obj):
    scores_array = get_tourism_scores_array(obj)
    _count_scores, _min_female_count, female_prefix = _get_standings_settings(obj)

    # В личной дистанции места считаем внутри возрастной группы.
    grouped_results = {}

    for result in getattr(obj, 'results', []):
        person = getattr(result, 'person', None)
        if not person or not person.group:
            continue

        grouped_results.setdefault(str(person.group.id), []).append(result)

    team_items: Dict[str, List[TourismTeamScoreItem]] = {}

    for _group_id, results in grouped_results.items():
        results = sorted(results, key=_sort_result_key)

        current_place = 0
        previous_time = None
        counted = 0

        for result in results:
            if not result.is_status_ok():
                continue

            result_time = result.get_result_otime().to_msec()
            if result_time <= 0:
                continue

            counted += 1

            if previous_time is None or result_time != previous_time:
                current_place = counted
                previous_time = result_time

            scores = get_score_by_place(scores_array, current_place)
            team_name = _team_name_from_person(result.person)
            group_name = _group_name_from_person(result.person)
            is_female = _is_female_group_name(group_name, female_prefix)

            detail = f'{result.person.full_name} [{group_name}]: {current_place} место, {scores} очк.'
            team_items.setdefault(team_name, []).append(
                TourismTeamScoreItem(
                    scores=scores,
                    detail=detail,
                    is_female=is_female,
                )
            )

    return _standing_rows(team_items, obj)


def _build_team_unit_standings(obj):
    _count_scores, _min_female_count, female_prefix = _get_standings_settings(obj)
    units = calculate_tourism_team_places_and_scores(obj)

    team_items: Dict[str, List[TourismTeamScoreItem]] = {}

    for unit in units:
        scores = int(getattr(unit, 'tourism_scores', 0) or 0)
        if scores <= 0:
            continue

        team_name = unit.team_name or 'Без коллектива'
        group_name = unit.group_name or ''
        is_female = _is_female_group_name(group_name, female_prefix)

        place = getattr(unit, 'place', '')
        detail = f'№{unit.number} [{group_name}]: {place} место, {scores} очк. ({unit.members_text})'

        team_items.setdefault(team_name, []).append(
            TourismTeamScoreItem(
                scores=scores,
                detail=detail,
                is_female=is_female,
            )
        )

    return _standing_rows(team_items, obj)


def build_tourism_overall_standings(obj=None) -> List[TourismStandingRow]:
    obj = obj or race()
    competition_type = getattr(obj, 'competition_type', '')

    if competition_type in TOURISM_TEAM_TYPES:
        return _build_team_unit_standings(obj)

    return _build_individual_standings(obj)
