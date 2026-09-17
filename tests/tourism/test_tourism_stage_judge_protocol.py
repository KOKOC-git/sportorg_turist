from sportorg.common.template import get_text_from_file


def test_stage_judge_protocol_template_renders():
    race = {
        'data': {
            'title': 'Tourism event',
            'start_datetime': '2026-09-12 10:00:00',
            'location': 'Park',
            'secretary': 'Secretary',
        },
        'persons': [],
        'groups': [],
        'organizations': [],
        'results': [],
        'courses': [],
        'tourism_courses': [],
        'tourism_stages': [],
    }

    html = get_text_from_file(
        '/reports/tourism/3_протокол_судьи_на_этапе.html',
        race=race,
    )

    assert 'ПРОТОКОЛ СУДЬИ НА ЭТАПЕ' in html
    assert 'Прохождение этапа' in html
    assert 'Штраф (время / баллы)' in html
    assert 'manual-stage' in html
