from __future__ import annotations

from collections import defaultdict

from sportorg.common.otime import OTime
from sportorg.models.tourism import CompetitionType, ensure_tourism_defaults


def _otime_to_msec(value) -> int:
    if value is None:
        return 0
    if hasattr(value, "to_msec"):
        return int(value.to_msec())
    return 0


def _make_otime_from_msec(value: int) -> OTime:
    return OTime(msec=max(0, int(value)))


class TourismResultCalculator:
    @staticmethod
    def apply(r):
        ensure_tourism_defaults(r)

        # Пока отдельная настройка не вынесена в интерфейс,
        # используем безопасное значение по умолчанию:
        # 1 штрафной балл = 30 секунд.
        penalty_point_sec = int(getattr(r, "tourism_penalty_point_sec", 30) or 30)

        for result in r.results:
            if not hasattr(result, "tourism_penalty_time"):
                continue

            if result._tourism_base_penalty_time is None:
                result._tourism_base_penalty_time = result.penalty_time
            if result._tourism_base_credit_time is None:
                result._tourism_base_credit_time = result.credit_time

            # score snapshots keep the original non-tourism values
            result._tourism_base_scores = getattr(result, "_tourism_base_scores", result.scores) or result.scores
            result._tourism_base_rogaine_score = getattr(result, "_tourism_base_rogaine_score", result.rogaine_score) or result.rogaine_score
            result._tourism_base_scores_ardf = getattr(result, "_tourism_base_scores_ardf", result.scores_ardf) or result.scores_ardf

            result.tourism_penalty_time = OTime()
            result.tourism_credit_time = OTime()
            result.tourism_penalty_points = 0
            result.tourism_stage_dsq_count = 0

            # Каждый пересчёт начинается с чистых базовых значений,
            # чтобы штрафы/отсечки не накапливались повторно.
            result.penalty_time = result._tourism_base_penalty_time
            result.credit_time = result._tourism_base_credit_time
            result.scores = result._tourism_base_scores
            result.rogaine_score = result._tourism_base_rogaine_score
            result.scores_ardf = result._tourism_base_scores_ardf

        if r.competition_type != CompetitionType.TOURISM.value:
            return

        result_map = {}
        for result in r.results:
            if result.person:
                result_map[str(result.person.id)] = result

        aggregates = defaultdict(lambda: {
            "penalty_time_sec": 0,
            "penalty_points": 0,
            "cutoff_time_sec": 0,
            "stage_dsq_count": 0,
        })

        for decision in r.tourism_stage_decisions:
            agg = aggregates[str(decision.person_id)]
            agg["cutoff_time_sec"] += int(decision.cutoff_time_sec)

            if decision.is_stage_dsq:
                agg["stage_dsq_count"] += 1
                continue

            agg["penalty_time_sec"] += int(decision.penalty_time_sec)
            agg["penalty_points"] += int(decision.penalty_points)

        for person_id, agg in aggregates.items():
            result = result_map.get(person_id)
            if not result:
                continue

            # В Excel-логике туризма штрафные баллы должны влиять на итоговое время.
            points_as_time_sec = int(agg["penalty_points"]) * penalty_point_sec
            total_tourism_penalty_sec = int(agg["penalty_time_sec"]) + points_as_time_sec

            result.tourism_penalty_time = OTime(msec=total_tourism_penalty_sec * 1000)
            result.tourism_credit_time = OTime(msec=int(agg["cutoff_time_sec"]) * 1000)
            result.tourism_penalty_points = int(agg["penalty_points"])
            result.tourism_stage_dsq_count = int(agg["stage_dsq_count"])

            base_penalty_msec = _otime_to_msec(result._tourism_base_penalty_time)
            base_credit_msec = _otime_to_msec(result._tourism_base_credit_time)

            # Ключевая интеграция со стандартным расчётом SportOrg:
            # penalty_time увеличивает результат,
            # credit_time уменьшает результат как отсечка.
            result.penalty_time = _make_otime_from_msec(
                base_penalty_msec + total_tourism_penalty_sec * 1000
            )
            result.credit_time = _make_otime_from_msec(
                base_credit_msec + int(agg["cutoff_time_sec"]) * 1000
            )

            # Очковую часть пока сохраняем для дисциплин, где результат считается баллами.
            # Для временного протокола основное влияние уже сделано через penalty_time.
            if agg["penalty_points"]:
                result.scores = max(0, result.scores - agg["penalty_points"])
                result.rogaine_score = max(0, result.rogaine_score - agg["penalty_points"])
                result.scores_ardf = max(0, result.scores_ardf - agg["penalty_points"])


def patch_result_calculation():
    from sportorg.models.result.result_calculation import ResultCalculation

    if getattr(ResultCalculation, "_tourism_patched", False):
        return

    original_process_results = ResultCalculation.process_results

    def wrapped_process_results(self, *args, **kwargs):
        TourismResultCalculator.apply(self.race)
        return original_process_results(self, *args, **kwargs)

    ResultCalculation.process_results = wrapped_process_results
    ResultCalculation._tourism_patched = True
