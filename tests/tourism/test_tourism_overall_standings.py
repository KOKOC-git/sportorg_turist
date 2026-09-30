from types import SimpleNamespace

import sportorg.services.tourism_overall_standings as standings
from sportorg.common.otime import OTime


class RaceStub:
    competition_type = 'tourism_group'

    def get_setting(self, _key, default=None):
        return default


def test_counted_results_include_required_female_result():
    items = [
        standings.TourismTeamScoreItem(scores=40, detail='М1'),
        standings.TourismTeamScoreItem(scores=37, detail='М2'),
        standings.TourismTeamScoreItem(scores=35, detail='Ж1', is_female=True),
    ]

    selected = standings._apply_team_score_rules(
        items, count_scores=2, min_female_count=1
    )

    assert [item.detail for item in selected] == ['М1', 'Ж1']
    assert sum(item.scores for item in selected) == 75


def test_missing_female_result_is_not_replaced_by_extra_male_result():
    items = [
        standings.TourismTeamScoreItem(scores=40, detail='М1'),
        standings.TourismTeamScoreItem(scores=37, detail='М2'),
        standings.TourismTeamScoreItem(scores=35, detail='М3'),
        standings.TourismTeamScoreItem(scores=33, detail='Ж1', is_female=True),
    ]

    selected = standings._apply_team_score_rules(
        items, count_scores=4, min_female_count=2
    )

    assert [item.detail for item in selected] == ['М1', 'М2', 'Ж1']
    assert sum(item.scores for item in selected) == 110


def test_territorial_standings_combine_all_groups_by_collective():
    units = [
        SimpleNamespace(number=1, group_name='М-ЮНИОРЫ', team_name='Север', tourism_scores=40, place=1, members_text='Иванов'),
        SimpleNamespace(number=2, group_name='М-КАДЕТЫ', team_name='Север', tourism_scores=37, place=2, members_text='Петров'),
        SimpleNamespace(number=3, group_name='Ж-ЮНИОРЫ', team_name='Север', tourism_scores=35, place=1, members_text='Сидорова'),
        SimpleNamespace(number=4, group_name='Ж-КАДЕТЫ', team_name='Юг', tourism_scores=33, place=1, members_text='Орлова'),
    ]

    class TerritorialRaceStub(RaceStub):
        def get_setting(self, key, default=None):
            values = {
                'tourism_standings_count_scores': 2,
                'tourism_standings_min_female_count': 1,
                'tourism_standings_female_group_prefix': 'Ж',
            }
            return values.get(key, default)

    original_builder = standings.calculate_tourism_team_places_and_scores
    standings.calculate_tourism_team_places_and_scores = lambda _obj: units
    try:
        rows = standings.build_tourism_territorial_standings(TerritorialRaceStub())
    finally:
        standings.calculate_tourism_team_places_and_scores = original_builder

    assert [row.team_name for row in rows] == ['Север', 'Юг']
    assert rows[0].scores == 75  # 40 (м) + 35 (ж), результат 37 не входит
    assert rows[0].unit_count == 2
    assert rows[0].place == 1
    assert rows[1].scores == 33


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


def test_individual_score_mode_uses_points_then_time_for_places():
    group = SimpleNamespace(name='М-МУЖ-ЖЕН_20-40')

    def make_result(name, organization, points, time_msec):
        person = SimpleNamespace(
            full_name=name,
            group=group,
            organization=SimpleNamespace(name=organization),
        )
        return SimpleNamespace(
            person=person,
            rogaine_score=points,
            tourism_stage_dsq_count=0,
            is_status_ok=lambda: True,
            get_result_otime=lambda: OTime(msec=time_msec),
        )

    results = [
        make_result('Быстрый, но меньше баллов', 'Команда 1', 69, 10 * 60_000),
        make_result('Медленный с 72 баллами', 'Команда 2', 72, 24 * 60_000),
        make_result('Быстрый с 72 баллами', 'Команда 3', 72, 13 * 60_000),
    ]

    class ScoreRaceStub(RaceStub):
        competition_type = 'tourism_individual'

        def __init__(self):
            self.results = results

        def get_setting(self, key, default=None):
            values = {
                'result_processing_mode': 'scores',
                'tourism_individual_scores_array': '40,37,35',
            }
            return values.get(key, default)

    rows = standings.build_tourism_overall_standings(ScoreRaceStub())
    rows_by_team = {row.team_name: row for row in rows}

    assert rows_by_team['Команда 3'].scores == 40
    assert rows_by_team['Команда 2'].scores == 37
    assert rows_by_team['Команда 1'].scores == 35
    assert '1 место, 40 очк.' in rows_by_team['Команда 3'].details
    assert '2 место, 37 очк.' in rows_by_team['Команда 2'].details
    assert '3 место, 35 очк.' in rows_by_team['Команда 1'].details


def test_equal_points_and_time_share_the_same_individual_place():
    group = SimpleNamespace(name='Ж-МУЖ-ЖЕН_20-40')

    def make_result(name, organization):
        return SimpleNamespace(
            person=SimpleNamespace(
                full_name=name,
                group=group,
                organization=SimpleNamespace(name=organization),
            ),
            rogaine_score=72,
            tourism_stage_dsq_count=0,
            is_status_ok=lambda: True,
            get_result_otime=lambda: OTime(msec=13 * 60_000),
        )

    class EqualScoreRaceStub(RaceStub):
        competition_type = 'tourism_individual'
        results = [make_result('Первая', 'Команда 1'), make_result('Вторая', 'Команда 2')]

        def get_setting(self, key, default=None):
            values = {
                'result_processing_mode': 'scores',
                'tourism_individual_scores_array': '40,37',
            }
            return values.get(key, default)

    rows = standings.build_tourism_overall_standings(EqualScoreRaceStub())

    assert [row.scores for row in rows] == [40, 40]
    assert all('1 место, 40 очк.' in row.details for row in rows)
