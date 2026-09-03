from types import SimpleNamespace

import sportorg.services.tourism_overall_standings as standings
from sportorg.common.otime import OTime


class RaceStub:
    competition_type = 'tourism_group'

    def get_setting(self, _key, default=None):
        return default


def test_team_unit_with_zero_scores_is_shown_without_place():
    unit = SimpleNamespace(
        number=7,
        group_name='М-ЮНИОРЫ',
        team_name='Команда Север',
        tourism_scores=0,
        place='',
        members_text='71 Иванов; 72 Петров',
    )
    original_builder = standings.calculate_tourism_team_places_and_scores
    standings.calculate_tourism_team_places_and_scores = lambda _obj: [unit]

    try:
        rows = standings.build_tourism_overall_standings(RaceStub())
    finally:
        standings.calculate_tourism_team_places_and_scores = original_builder

    assert len(rows) == 1
    assert rows[0].team_name == 'Команда Север'
    assert rows[0].scores == 0
    assert rows[0].place == ''
    assert rows[0].unit_count == 1
    assert 'без места, 0 очк.' in rows[0].details


def test_positive_and_zero_score_teams_are_sorted_and_placed_correctly():
    units = [
        SimpleNamespace(
            number=1,
            group_name='Ж-КАДЕТЫ',
            team_name='Команда Ноль',
            tourism_scores=0,
            place='',
            members_text='11 Участник',
        ),
        SimpleNamespace(
            number=2,
            group_name='М-КАДЕТЫ',
            team_name='Команда Лидер',
            tourism_scores=40,
            place=1,
            members_text='21 Победитель',
        ),
    ]
    original_builder = standings.calculate_tourism_team_places_and_scores
    standings.calculate_tourism_team_places_and_scores = lambda _obj: units

    try:
        rows = standings.build_tourism_overall_standings(RaceStub())
    finally:
        standings.calculate_tourism_team_places_and_scores = original_builder

    assert [row.team_name for row in rows] == ['Команда Лидер', 'Команда Ноль']
    assert [row.place for row in rows] == [1, '']
    assert [row.scores for row in rows] == [40, 0]


def test_individual_zero_score_team_is_shown_without_place():
    person = SimpleNamespace(
        full_name='Иванов Иван',
        group=SimpleNamespace(name='М-ЮНИОРЫ'),
        organization=SimpleNamespace(name='Команда Север'),
    )
    result = SimpleNamespace(
        person=person,
        is_status_ok=lambda: True,
        get_result_otime=lambda: OTime(msec=60_000),
    )

    class IndividualRaceStub(RaceStub):
        competition_type = 'tourism_individual'
        results = [result]

        def get_setting(self, key, default=None):
            if key == 'tourism_individual_scores_array':
                return '0'
            return default

    rows = standings.build_tourism_overall_standings(IndividualRaceStub())

    assert len(rows) == 1
    assert rows[0].team_name == 'Команда Север'
    assert rows[0].scores == 0
    assert rows[0].place == ''
