from __future__ import annotations

from .models import ResultStatus, ScoringMode, TourismResult, TourismSettings, sum_stage_values


def calculate_tourism_result(result: TourismResult, settings: TourismSettings) -> TourismResult:
    """Calculate tourism penalties, cut-offs and final time in seconds.

    Base rule copied from the existing Excel judging logic:
        final = finish - start - cutoffs + penalty_time

    Stage DQ is deliberately not treated as distance DQ. It is stored as a
    separate status and ranking can decide whether it receives a place.
    """
    penalty_points, cutoff_seconds, stage_dq_count, si_miss_count = sum_stage_values(result.stages)

    result.penalty_points_sum = 0 if settings.scoring_mode == ScoringMode.NO_PENALTY else penalty_points
    result.cutoff_sum_seconds = cutoff_seconds
    result.stage_dq_count = stage_dq_count
    result.si_miss_count = si_miss_count
    result.penalty_time_seconds = result.penalty_points_sum * max(0, int(settings.penalty_unit_seconds or 0))

    if not result.has_valid_time():
        result.pure_time_seconds = None
        result.final_time_seconds = None
        if result.status == ResultStatus.OK:
            result.status = ResultStatus.NOT_FINISHED
        return result

    result.pure_time_seconds = max(0, int(result.finish_seconds) - int(result.start_seconds))
    result.final_time_seconds = max(
        0,
        result.pure_time_seconds - result.cutoff_sum_seconds + result.penalty_time_seconds,
    )

    if result.status == ResultStatus.OK and stage_dq_count:
        result.status = ResultStatus.STAGE_DQ

    if (
        settings.auto_over_time_limit
        and settings.control_time_seconds is not None
        and result.final_time_seconds is not None
        and result.final_time_seconds > settings.control_time_seconds
        and result.status in (ResultStatus.OK, ResultStatus.STAGE_DQ)
    ):
        result.status = ResultStatus.OVER_TIME_LIMIT

    return result


def format_seconds(value: int | None) -> str:
    if value is None:
        return ""
    value = max(0, int(value))
    hours = value // 3600
    minutes = (value % 3600) // 60
    seconds = value % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
