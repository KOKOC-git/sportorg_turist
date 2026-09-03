from __future__ import annotations

import logging

from collections import defaultdict

from sportorg.common.otime import OTime
from sportorg.models.tourism import (
    CompetitionType,
    TOURISM_COMPETITION_TYPES,
    ensure_tourism_defaults,
)


def _otime_to_msec(value) -> int:
    if value is None:
        return 0
    if hasattr(value, "to_msec"):
        return int(value.to_msec())
    return 0


def _make_otime_from_msec(value: int) -> OTime:
    return OTime(msec=max(0, int(value)))


def _debug_otime(value) -> str:
    if value is None:
        return "None"
    if hasattr(value, "to_msec"):
        try:
            return f"{value.to_str()} / {value.to_msec()} ms"
        except Exception:
            return str(value)
    return str(value)


class TourismResultCalculator:
    @staticmethod
    def apply(r):
        ensure_tourism_defaults(r)

        logging.debug(
            "TOURISM CALC START: competition_type=%s, results=%s, decisions=%s",
            getattr(r, "competition_type", None),
            len(getattr(r, "results", [])),
            len(getattr(r, "tourism_stage_decisions", [])),
        )

        penalty_point_sec = int(getattr(r, "tourism_penalty_point_sec", 30) or 30)

        for result in r.results:
            if not hasattr(result, "tourism_penalty_time"):
                continue

            # В режиме Туризм penalty_time и credit_time являются вычисляемыми полями.
            # Они не должны использоваться как база, потому что при сохранении файла
            # туда уже попадает результат предыдущего туристского пересчёта.
            # Иначе после открытия файла штрафы/отсечки начинают прибавляться повторно.
            if (
                getattr(r, "competition_type", CompetitionType.INDIVIDUAL.value)
                in TOURISM_COMPETITION_TYPES
            ):
                result._tourism_base_penalty_time = OTime()
                result._tourism_base_credit_time = OTime()
            else:
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

        if r.competition_type not in TOURISM_COMPETITION_TYPES:
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

        # Защита от дублей: по одному участнику и одному этапу
        # должна учитываться только одна, последняя запись.
        # Иначе при повторном сохранении штраф/отсечка могут суммироваться несколько раз.
        unique_decisions = {}
        for decision in getattr(r, "tourism_stage_decisions", []):
            key = (str(decision.person_id), str(decision.stage_id))
            unique_decisions[key] = decision

        # Также очищаем список в памяти, чтобы при следующем сохранении файл не хранил дубли.
        r.tourism_stage_decisions = list(unique_decisions.values())

        for decision in unique_decisions.values():
            agg = aggregates[str(decision.person_id)]
            agg["cutoff_time_sec"] += int(decision.cutoff_time_sec)

            if decision.is_stage_dsq:
                agg["stage_dsq_count"] += 1
                continue

            if getattr(r, 'tourism_judging_mode', 'penalty') == 'no_penalty':
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
            # В стандартный расчёт SportOrg передаём не две величины сразу,
            # а чистую разницу: штрафы минус отсечки.
            # Иначе в некоторых режимах SportOrg применяет credit_time,
            # но не прибавляет penalty_time к итоговому времени.
            net_tourism_msec = (
                total_tourism_penalty_sec * 1000
                - int(agg["cutoff_time_sec"]) * 1000
            )

            if net_tourism_msec >= 0:
                result.penalty_time = _make_otime_from_msec(
                    base_penalty_msec + net_tourism_msec
                )
                result.credit_time = _make_otime_from_msec(base_credit_msec)
            else:
                result.penalty_time = _make_otime_from_msec(base_penalty_msec)
                result.credit_time = _make_otime_from_msec(
                    base_credit_msec + abs(net_tourism_msec)
                )

            logging.debug(
                "TOURISM RESULT AFTER APPLY: person_id=%s penalty_time_sec=%s penalty_points=%s cutoff_time_sec=%s stage_dsq_count=%s final_penalty=%s final_credit=%s tourism_penalty=%s tourism_credit=%s",
                person_id,
                agg["penalty_time_sec"],
                agg["penalty_points"],
                agg["cutoff_time_sec"],
                agg["stage_dsq_count"],
                _debug_otime(result.penalty_time),
                _debug_otime(result.credit_time),
                _debug_otime(result.tourism_penalty_time),
                _debug_otime(result.tourism_credit_time),
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
        # 1. Сначала применяем туристские штрафы/отсечки,
        # чтобы стандартный расчёт SportOrg посчитал итоговое время с ними.
        TourismResultCalculator.apply(self.race)

        result = original_process_results(self, *args, **kwargs)

        import logging
        for r in getattr(self.race, 'results', []):
            if getattr(r, 'person', None):
                penalty = getattr(r, 'penalty_time', None)
                credit = getattr(r, 'credit_time', None)
                logging.debug(
                    'TOURISM AFTER STANDARD PROCESS: person=%s result=%s penalty=%s/%s credit=%s/%s tourism_penalty=%s tourism_credit=%s',
                    getattr(r.person, 'full_name', ''),
                    r.get_result() if hasattr(r, 'get_result') else '',
                    penalty,
                    penalty.to_msec() if penalty and hasattr(penalty, 'to_msec') else None,
                    credit,
                    credit.to_msec() if credit and hasattr(credit, 'to_msec') else None,
                    getattr(r, 'tourism_penalty_time', None),
                    getattr(r, 'tourism_credit_time', None),
                )

        # 2. После стандартного расчёта SportOrg может повторно менять
        # penalty_time / credit_time. Поэтому возвращаем итоговые туристские
        # значения ещё раз, но уже без повторного запуска ResultCalculation.
        TourismResultCalculator.apply(self.race)

        return result

    ResultCalculation.process_results = wrapped_process_results
    ResultCalculation._tourism_patched = True
