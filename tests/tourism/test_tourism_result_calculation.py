from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Group,
    Person,
    Race,
    ResultManual,
    ResultStatus,
    new_event,
)
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.tourism import TourismStageDecision
from sportorg.services.tourism_result_calculation import TourismResultCalculator


def make_tourism_race(competition_type='tourism_individual'):
    race_obj = Race()
    race_obj.competition_type = competition_type

    person = Person()
    person.name = 'Иван'
    person.surname = 'Иванов'

    result = ResultManual()
    result.person = person
    result.start_time = OTime(msec=10 * 60 * 60 * 1000)
    result.finish_time = OTime(msec=(10 * 60 * 60 + 30 * 60) * 1000)

    race_obj.persons.append(person)
    race_obj.results.append(result)
    return race_obj, person, result


def add_decision(race_obj, person, **values):
    decision = TourismStageDecision(
        stage_id=values.pop('stage_id', 'stage-1'),
        person_id=str(person.id),
        **values,
    )
    race_obj.tourism_stage_decisions.append(decision)
    return decision


def test_live_calculator_combines_time_points_and_cutoff():
    race_obj, person, result = make_tourism_race()
    add_decision(
        race_obj,
        person,
        penalty_time_sec=60,
        penalty_points=2,
        cutoff_time_sec=30,
    )

    TourismResultCalculator.apply(race_obj)

    assert result.tourism_penalty_time.to_msec() == 120_000
    assert result.tourism_credit_time.to_msec() == 30_000
    assert result.tourism_penalty_points == 2
    assert result.penalty_time.to_msec() == 90_000
    assert result.credit_time.to_msec() == 0


def test_live_calculator_uses_configured_penalty_point_value():
    race_obj, person, result = make_tourism_race()
    race_obj.tourism_penalty_point_sec = 45
    add_decision(race_obj, person, penalty_points=2)

    TourismResultCalculator.apply(race_obj)

    assert result.tourism_penalty_time.to_msec() == 90_000
    assert result.penalty_time.to_msec() == 90_000


def test_penalty_point_value_is_serialized():
    race_obj = Race()
    race_obj.tourism_penalty_point_sec = 45

    serialized = race_obj.to_dict()

    assert serialized['tourism_penalty_point_sec'] == 45


def test_live_calculator_is_idempotent():
    race_obj, person, result = make_tourism_race()
    add_decision(race_obj, person, penalty_time_sec=60, cutoff_time_sec=15)

    TourismResultCalculator.apply(race_obj)
    first_penalty = result.penalty_time.to_msec()
    first_credit = result.credit_time.to_msec()

    TourismResultCalculator.apply(race_obj)

    assert result.penalty_time.to_msec() == first_penalty == 45_000
    assert result.credit_time.to_msec() == first_credit == 0


def test_live_calculator_keeps_cutoff_when_it_exceeds_penalty():
    race_obj, person, result = make_tourism_race()
    add_decision(race_obj, person, penalty_time_sec=30, cutoff_time_sec=90)

    TourismResultCalculator.apply(race_obj)

    assert result.penalty_time.to_msec() == 0
    assert result.credit_time.to_msec() == 60_000


def test_live_calculator_counts_stage_dsq_without_distance_dsq():
    race_obj, person, result = make_tourism_race()
    add_decision(race_obj, person, is_stage_dsq=True)

    TourismResultCalculator.apply(race_obj)

    assert result.tourism_stage_dsq_count == 1
    assert result.is_status_ok()
    assert result.penalty_time.to_msec() == 0


def test_no_penalty_mode_ignores_penalties_but_keeps_cutoff():
    race_obj, person, result = make_tourism_race()
    race_obj.tourism_judging_mode = 'no_penalty'
    add_decision(
        race_obj,
        person,
        penalty_time_sec=60,
        penalty_points=2,
        cutoff_time_sec=30,
    )

    TourismResultCalculator.apply(race_obj)

    assert result.tourism_penalty_time.to_msec() == 0
    assert result.tourism_penalty_points == 0
    assert result.penalty_time.to_msec() == 0
    assert result.credit_time.to_msec() == 30_000


def test_live_calculator_uses_latest_duplicate_decision():
    race_obj, person, result = make_tourism_race()
    add_decision(race_obj, person, stage_id='stage-1', penalty_time_sec=30)
    latest = add_decision(
        race_obj,
        person,
        stage_id='stage-1',
        penalty_time_sec=90,
    )

    TourismResultCalculator.apply(race_obj)

    assert result.penalty_time.to_msec() == 90_000
    assert race_obj.tourism_stage_decisions == [latest]


def test_all_tourism_competition_types_use_live_calculator():
    for competition_type in (
        'tourism',
        'tourism_individual',
        'tourism_pair',
        'tourism_group',
    ):
        race_obj, person, result = make_tourism_race(competition_type)
        add_decision(race_obj, person, penalty_time_sec=30)

        TourismResultCalculator.apply(race_obj)

        assert result.penalty_time.to_msec() == 30_000, competition_type


def test_stage_dsq_results_are_sorted_after_clean_results():
    race_obj = Race()
    race_obj.competition_type = 'tourism_individual'
    new_event([race_obj])

    clean_person = Person()
    stage_dsq_person = Person()
    clean_result = ResultManual()
    stage_dsq_result = ResultManual()
    clean_result.person = clean_person
    stage_dsq_result.person = stage_dsq_person
    clean_result.start_time = OTime(msec=0)
    stage_dsq_result.start_time = OTime(msec=0)
    clean_result.finish_time = OTime(msec=40 * 60 * 1000)
    stage_dsq_result.finish_time = OTime(msec=20 * 60 * 1000)
    stage_dsq_result.tourism_stage_dsq_count = 1

    assert sorted([stage_dsq_result, clean_result]) == [clean_result, stage_dsq_result]


def test_stage_dsq_count_breaks_place_ties():
    race_obj = Race()
    race_obj.competition_type = 'tourism_group'
    new_event([race_obj])
    group = Group()

    clean_person = Person()
    clean_person.group = group
    stage_dsq_person = Person()
    stage_dsq_person.group = group
    clean_result = ResultManual()
    stage_dsq_result = ResultManual()

    for result, person in (
        (clean_result, clean_person),
        (stage_dsq_result, stage_dsq_person),
    ):
        result.person = person
        result.start_time = OTime(msec=0)
        result.finish_time = OTime(msec=30 * 60 * 1000)

    stage_dsq_result.tourism_stage_dsq_count = 1
    ordered = sorted([stage_dsq_result, clean_result])
    ResultCalculation(race_obj).set_places(ordered)

    assert ordered == [clean_result, stage_dsq_result]
    assert clean_result.place == 1
    assert stage_dsq_result.place == 2


def test_non_finisher_stays_after_ok_result_with_stage_dsq():
    race_obj = Race()
    race_obj.competition_type = 'tourism_pair'
    new_event([race_obj])

    ok_result = ResultManual()
    ok_result.person = Person()
    ok_result.tourism_stage_dsq_count = 1
    non_finisher = ResultManual()
    non_finisher.person = Person()
    non_finisher.status = ResultStatus.DID_NOT_FINISH

    assert sorted([non_finisher, ok_result]) == [ok_result, non_finisher]
