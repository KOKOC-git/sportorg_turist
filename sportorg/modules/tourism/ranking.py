from __future__ import annotations

from typing import Iterable, List, Optional

from .models import ResultStatus, TourismResult, TourismSettings


_STATUS_ORDER = {
    ResultStatus.OK: 0,
    ResultStatus.STAGE_DQ: 1,
    ResultStatus.OVER_TIME_LIMIT: 2,
    ResultStatus.NOT_FINISHED: 3,
    ResultStatus.DISTANCE_DQ: 4,
    ResultStatus.OUT_OF_COMPETITION: 5,
}


def _is_placeable(result: TourismResult, settings: TourismSettings) -> bool:
    if result.status == ResultStatus.OK:
        return result.final_time_seconds is not None
    if result.status == ResultStatus.STAGE_DQ:
        return settings.stage_dq_gets_place and result.final_time_seconds is not None
    return False


def _sort_key(result: TourismResult) -> tuple:
    missing_time = 1 if result.final_time_seconds is None else 0
    final_time = result.final_time_seconds if result.final_time_seconds is not None else 10**12
    return (
        _STATUS_ORDER.get(result.status, 99),
        result.stage_dq_count,
        missing_time,
        final_time,
        result.penalty_points_sum,
        result.si_miss_count,
        result.name.lower(),
    )


def rank_tourism_results(results: Iterable[TourismResult], settings: TourismSettings) -> List[TourismResult]:
    ranked = sorted(results, key=_sort_key)
    place = 1
    previous_key: Optional[tuple] = None
    previous_place: Optional[int] = None

    for result in ranked:
        if not _is_placeable(result, settings):
            result.place = None
            continue

        tie_key = (result.final_time_seconds, result.penalty_points_sum, result.stage_dq_count)
        if previous_key == tie_key and previous_place is not None:
            result.place = previous_place
        else:
            result.place = place
            previous_place = place
            previous_key = tie_key
        place += 1

    return ranked
