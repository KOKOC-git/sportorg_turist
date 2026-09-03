from datetime import datetime
from typing import Iterable, List, Mapping

from sportorg.models.tourism import TourismJudgingMode, TourismStageDecision


def build_updated_tourism_decisions(
    existing_decisions: Iterable[TourismStageDecision],
    updates: Iterable[Mapping],
    judging_mode: TourismJudgingMode,
) -> List[TourismStageDecision]:
    """Validate a batch and return a new decision list without partial mutation."""
    existing_by_key = {}
    for decision in existing_decisions:
        key = (str(decision.person_id), str(decision.stage_id))
        existing_by_key[key] = decision

    prepared_updates = {}
    update_order = []

    for row_number, values in enumerate(updates, 1):
        person_id = str(values.get('person_id', ''))
        stage_id = str(values.get('stage_id', ''))
        key = (person_id, stage_id)
        update_order.append(key)

        penalty_time_sec = int(values.get('penalty_time_sec', 0) or 0)
        penalty_points = int(values.get('penalty_points', 0) or 0)
        cutoff_time_sec = int(values.get('cutoff_time_sec', 0) or 0)
        is_stage_dsq = bool(values.get('is_stage_dsq', False))
        comment = str(values.get('comment', '') or '').strip()

        is_empty = (
            not is_stage_dsq
            and penalty_time_sec == 0
            and penalty_points == 0
            and cutoff_time_sec == 0
            and not comment
        )
        if is_empty:
            prepared_updates[key] = None
            continue

        existing = existing_by_key.get(key)
        decision = (
            TourismStageDecision.from_dict(existing.to_dict())
            if existing
            else TourismStageDecision(stage_id=stage_id, person_id=person_id)
        )
        decision.penalty_time_sec = penalty_time_sec
        decision.penalty_points = penalty_points
        decision.cutoff_time_sec = cutoff_time_sec
        decision.is_stage_dsq = is_stage_dsq
        decision.comment = comment
        decision.updated_at = datetime.utcnow().isoformat()

        try:
            decision.validate(judging_mode)
        except Exception as error:
            raise ValueError(f'Строка {row_number}: {error}') from error

        prepared_updates[key] = decision

    result = [
        decision
        for key, decision in existing_by_key.items()
        if key not in prepared_updates
    ]
    added_keys = set()
    for key in update_order:
        decision = prepared_updates[key]
        if decision is not None and key not in added_keys:
            result.append(decision)
            added_keys.add(key)

    return result
