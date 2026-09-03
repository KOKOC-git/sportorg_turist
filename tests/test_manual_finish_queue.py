from sportorg.common.otime import OTime
from sportorg.models.memory import Person, Race, ResultManual
from sportorg.services.manual_finish_queue import (
    add_pending_finish,
    assign_bib_to_finish,
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
    assert restored.pending_manual_finishes[0]['arrival_order'] == 1


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
    assert race_obj.pending_manual_finishes[0]['arrival_order'] == 1


def test_invalid_finish_is_skipped_and_assigned_finish_is_restored():
    race_obj = Race()
    data = race_obj.to_dict()
    data['pending_manual_finishes'] = [
        {'id': 'bad', 'finish_time_msec': 'not-a-time', 'status': 'pending'},
        {
            'id': 'done',
            'arrival_order': 2,
            'finish_time_msec': 1000,
            'status': 'assigned',
            'bib': 17,
        },
    ]

    race_obj.update_data(data)

    assert len(race_obj.pending_manual_finishes) == 1
    assert race_obj.pending_manual_finishes[0]['id'] == 'done'
    assert race_obj.pending_manual_finishes[0]['bib'] == 17


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
    assert len(race_obj.pending_manual_finishes) == 1
    assert race_obj.pending_manual_finishes[0]['arrival_order'] == 1
    assert race_obj.pending_manual_finishes[0]['status'] == 'assigned'
    assert race_obj.pending_manual_finishes[0]['bib'] == 17

    serialized = result.to_dict()
    restored_result = ResultManual()
    restored_result.update_data(serialized)
    assert restored_result.finish_event_id == item['id']
    assert restored_result.finish_source == 'moxa'
    assert restored_result.finish_raw == '2a'


def test_arrival_order_continues_after_assigned_finishes():
    race_obj = Race()
    first = add_pending_finish(race_obj, OTime(msec=1000))
    second = add_pending_finish(race_obj, OTime(msec=2000))
    first['status'] = 'assigned'
    first['bib'] = 10

    third = add_pending_finish(race_obj, OTime(msec=3000))

    assert [first['arrival_order'], second['arrival_order'], third['arrival_order']] == [
        1,
        2,
        3,
    ]


def test_selected_finish_can_be_assigned_out_of_order_and_corrected():
    race_obj = Race()
    first_person = Person()
    first_person.set_bib(31)
    corrected_person = Person()
    corrected_person.set_bib(32)
    race_obj.add_person(first_person)
    race_obj.add_person(corrected_person)

    first_mark = add_pending_finish(race_obj, OTime(msec=1000))
    second_mark = add_pending_finish(race_obj, OTime(msec=2000))

    result = assign_bib_to_finish(race_obj, second_mark['id'], 31)

    assert first_mark['status'] == 'pending'
    assert second_mark['status'] == 'assigned'
    assert second_mark['bib'] == 31
    assert result.finish_time.to_msec() == 2000

    corrected_result = assign_bib_to_finish(race_obj, second_mark['id'], 32)

    assert corrected_result is result
    assert len(race_obj.results) == 1
    assert result.person is corrected_person
    assert result.bib == 32
    assert second_mark['bib'] == 32
