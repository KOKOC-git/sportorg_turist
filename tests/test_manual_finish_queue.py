from sportorg.common.otime import OTime
from sportorg.models.memory import Person, Race, ResultManual
from sportorg.services.manual_finish_queue import (
    add_pending_finish,
    assign_bib_to_oldest,
)


def test_pending_finish_is_serialized_and_restored():
    race_obj = Race()
    item = add_pending_finish(
        race_obj,
        OTime(msec=12_345),
        source='moxa',
        raw='2a0d0a',
    )

    data = race_obj.to_dict()
    restored = Race()
    data['id'] = str(restored.id)
    restored.update_data(data)

    assert restored.pending_manual_finishes == [item]


def test_old_pending_finish_gets_compatible_metadata_defaults():
    race_obj = Race()
    data = race_obj.to_dict()
    data['pending_manual_finishes'] = [
        {
            'id': 'old-event',
            'finish_time_msec': 54_321,
            'status': 'pending',
        }
    ]

    race_obj.update_data(data)

    assert race_obj.pending_manual_finishes[0]['source'] == 'manual'
    assert race_obj.pending_manual_finishes[0]['raw'] == ''


def test_invalid_and_already_assigned_finishes_are_not_restored():
    race_obj = Race()
    data = race_obj.to_dict()
    data['pending_manual_finishes'] = [
        {'id': 'bad', 'finish_time_msec': 'not-a-time', 'status': 'pending'},
        {'id': 'done', 'finish_time_msec': 1000, 'status': 'assigned'},
    ]

    race_obj.update_data(data)

    assert race_obj.pending_manual_finishes == []


def test_assigning_finish_preserves_event_audit_data_in_result():
    race_obj = Race()
    person = Person()
    person.set_bib(17)
    race_obj.add_person(person)
    item = add_pending_finish(
        race_obj,
        OTime(msec=98_765),
        source='moxa',
        raw='2a',
    )

    result = assign_bib_to_oldest(race_obj, 17)

    assert isinstance(result, ResultManual)
    assert result.finish_time.to_msec() == 98_765
    assert result.finish_event_id == item['id']
    assert result.finish_source == 'moxa'
    assert result.finish_raw == '2a'
    assert race_obj.pending_manual_finishes == []

    serialized = result.to_dict()
    restored_result = ResultManual()
    restored_result.update_data(serialized)
    assert restored_result.finish_event_id == item['id']
    assert restored_result.finish_source == 'moxa'
    assert restored_result.finish_raw == '2a'
