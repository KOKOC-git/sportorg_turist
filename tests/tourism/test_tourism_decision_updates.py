from sportorg.models.tourism import TourismJudgingMode, TourismStageDecision
from sportorg.services.tourism_decision_updates import (
    build_updated_tourism_decisions,
)


def test_batch_update_does_not_mutate_existing_decisions_on_error():
    existing = TourismStageDecision(
        stage_id='stage-1',
        person_id='person-1',
        penalty_time_sec=30,
    )
    original_data = existing.to_dict()
    updates = [
        {
            'stage_id': 'stage-1',
            'person_id': 'person-1',
            'penalty_time_sec': 60,
        },
        {
            'stage_id': 'stage-2',
            'person_id': 'person-1',
            'penalty_time_sec': 30,
            'penalty_points': 1,
        },
    ]

    try:
        build_updated_tourism_decisions(
            [existing],
            updates,
            TourismJudgingMode.PENALTY,
        )
    except ValueError as error:
        assert 'Строка 2' in str(error)
    else:
        raise AssertionError('Пакет с ошибочной строкой должен быть отклонён')

    assert existing.to_dict() == original_data


def test_batch_update_replaces_clears_and_preserves_decisions():
    replaced = TourismStageDecision(
        stage_id='stage-1',
        person_id='person-1',
        penalty_time_sec=30,
    )
    cleared = TourismStageDecision(
        stage_id='stage-2',
        person_id='person-1',
        penalty_time_sec=30,
    )
    untouched = TourismStageDecision(
        stage_id='stage-3',
        person_id='person-2',
        penalty_time_sec=15,
    )

    result = build_updated_tourism_decisions(
        [replaced, cleared, untouched],
        [
            {
                'stage_id': 'stage-1',
                'person_id': 'person-1',
                'penalty_time_sec': 90,
            },
            {
                'stage_id': 'stage-2',
                'person_id': 'person-1',
            },
        ],
        TourismJudgingMode.PENALTY,
    )

    by_key = {(item.person_id, item.stage_id): item for item in result}
    assert len(result) == 2
    assert by_key[('person-1', 'stage-1')].penalty_time_sec == 90
    assert ('person-1', 'stage-2') not in by_key
    assert by_key[('person-2', 'stage-3')] is untouched
    assert replaced.penalty_time_sec == 30
