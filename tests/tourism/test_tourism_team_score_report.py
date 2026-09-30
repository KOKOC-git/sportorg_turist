from types import SimpleNamespace

from sportorg.common.template import get_text_from_file
from sportorg.common.otime import OTime
from sportorg.models.memory import Person, Race, ResultManual
from sportorg.services.tourism_team_units import build_tourism_team_units


def test_tourism_team_score_report_renders_current_service_data():
    unit = SimpleNamespace(place=1, number=7, members_text='71 Иванов; 72 Петров', group_name='М-ЮНИОРЫ', team_name='Команда Север', result_text='00:12:34', status_text='OK', tourism_scores=40, warning_text='')
    standing = SimpleNamespace(place=1, group_name='ЮНИОРЫ', team_name='Команда Север', scores=77, unit_count=2, details='№7: 1 место, 40 очк.; №8: 2 место, 37 очк.')
    race = {'data': {'description': 'Турслёт', 'start_datetime': '2026-09-26 10:00:00', 'location': 'Полигон'}, 'persons': [], 'groups': [], 'organizations': [], 'results': [], 'courses': []}

    territorial = SimpleNamespace(place=1, team_name='Команда Север', scores=110, unit_count=3, details='Три лучших результата')
    html = get_text_from_file('/reports/tourism/team_score.html', race=race, tourism_team_units=[unit], tourism_standings=[standing], tourism_territorial_standings=[territorial], tourism_standings_rules={'count_scores': 2, 'min_female_count': 1, 'female_prefix': 'Ж'})

    assert 'РЕЗУЛЬТАТЫ СВЯЗОК / ГРУПП' in html
    assert '71 Иванов; 72 Петров' in html
    assert 'КОМАНДНЫЙ ПРОТОКОЛ — ТУРИЗМ' in html
    assert 'Команда Север' in html
    assert '77' in html
    assert 'Состав зачётных результатов' in html
    assert '2 лучших результатов' in html
    assert 'женских — не менее 1' in html
    assert 'признак женской группы — «Ж»' in html
    assert 'ТЕРРИТОРИАЛЬНЫЙ ЗАЧЁТ' in html
    assert 'Коллектив / территория' in html
    assert '110' in html


def test_old_group_event_without_team_numbers_keeps_start_units():
    race = Race()
    race.competition_type = 'tourism_group'
    person = Person()
    person.set_bib(17)
    result = ResultManual()
    result.person = person
    result.start_time = OTime(msec=10 * 60 * 60 * 1000)
    result.finish_time = OTime(msec=(10 * 60 * 60 + 12 * 60) * 1000)
    race.persons.append(person)
    race.results.append(result)

    units = build_tourism_team_units(race)

    assert len(units) == 1
    assert units[0].number == 17
    assert units[0].persons == [person]
    assert units[0].result is result
