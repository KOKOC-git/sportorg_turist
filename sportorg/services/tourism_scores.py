from typing import List

from sportorg.models.memory import race
from sportorg.services.tourism_team_units import build_tourism_team_units


DEFAULT_TOURISM_SCORES = '40,37,35,33,32,31,30,29,28,27,26,25,24,23,22,21,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1'


def parse_scores_array(text: str) -> List[int]:
    values = []

    for part in str(text or '').replace(';', ',').split(','):
        part = part.strip()
        if not part:
            continue

        try:
            values.append(int(part))
        except Exception:
            continue

    return values


def get_score_by_place(scores: List[int], place: int) -> int:
    if place <= 0 or not scores:
        return 0

    if place <= len(scores):
        return scores[place - 1]

    return scores[-1]


def get_tourism_scores_setting_key(obj=None) -> str:
    obj = obj or race()
    competition_type = getattr(obj, 'competition_type', '')

    if competition_type == 'tourism_pair':
        return 'tourism_pair_scores_array'

    if competition_type == 'tourism_group':
        return 'tourism_group_scores_array'

    return 'tourism_individual_scores_array'


def get_tourism_scores_array(obj=None) -> List[int]:
    obj = obj or race()
    key = get_tourism_scores_setting_key(obj)
    return parse_scores_array(obj.get_setting(key, DEFAULT_TOURISM_SCORES))


def _unit_sort_key(unit):
    result = unit.result

    if result is None:
        return (1, 999999999999, unit.number)

    if not result.is_status_ok():
        return (1, 999999999999, unit.number)

    result_time = result.get_result_otime().to_msec()
    if result_time <= 0:
        return (1, 999999999999, unit.number)

    return (0, result_time, unit.number)


def calculate_tourism_team_places_and_scores(obj=None):
    obj = obj or race()
    scores_array = get_tourism_scores_array(obj)

    units = build_tourism_team_units(obj)
    units = sorted(units, key=_unit_sort_key)

    current_place = 0
    previous_time = None
    counted = 0

    for unit in units:
        unit.place = ''
        unit.tourism_scores = 0

        result = unit.result
        if result is None or not result.is_status_ok():
            continue

        result_time = result.get_result_otime().to_msec()
        if result_time <= 0:
            continue

        counted += 1

        if previous_time is None or result_time != previous_time:
            current_place = counted
            previous_time = result_time

        unit.place = current_place
        unit.tourism_scores = get_score_by_place(scores_array, current_place)

    return units
