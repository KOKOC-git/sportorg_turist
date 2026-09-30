from sportorg.common.template import get_text_from_file


def test_tourism_start_protocol_renders_editable_full_table():
    race = {
        'data': {
            'description': 'Туристский слёт',
            'start_datetime': '2026-09-26 10:00:00',
            'location': 'Полигон',
            'chief_referee': 'Главный судья',
            'secretary': 'Секретарь',
        },
        'persons': [], 'groups': [], 'organizations': [], 'results': [],
        'courses': [], 'tourism_courses': [], 'tourism_stages': [],
    }

    html = get_text_from_file(
        '/reports/tourism/2_стартовый_протокол.html', race=race
    )

    assert 'СТАРТОВЫЙ ПРОТОКОЛ — ТУРИЗМ' in html
    assert 'Участник / команда' in html
    assert 'Фактический старт' in html
    assert 'Отметка судьи' in html
    assert 'contentEditable' in html
    assert 'Настройка протокола перед печатью' in html
    assert "row.group || 'Без группы'" in html
    assert "groupTitle.textContent = 'Группа: ' + groupName" in html
    assert 'page-break-after: always' in html
    assert 'section.appendChild(createProtocolHeading(groupName))' in html
    assert 'section.appendChild(createSignatures())' in html
    assert 'document.querySelectorAll(\'.protocol-main-title\')' not in html
    assert 'white-space: normal !important' in html
    assert 'overflow-wrap: anywhere !important' in html
    assert 'page-break-before: auto !important' in html
    assert 'max-width: 100%' in html
    assert "race.competition_type === 'tourism_group' ? 'Состав группы'" in html
    assert 'function rowsFromTourismGroups()' in html
    assert 'person.tourism_team_number' in html
    assert "persons.map(personName).filter(Boolean).join('; ')" in html
