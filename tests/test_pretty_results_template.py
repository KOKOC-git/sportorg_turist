from pathlib import Path


def test_pretty_results_print_columns_stay_inside_cells():
    template = (
        Path(__file__).parents[1]
        / 'templates'
        / 'reports'
        / '1_протокол_результатов_красивый.html'
    ).read_text(encoding='utf-8')

    assert 'createResultsTable(rows, fields)' in template
    assert "cell.classList.add('field-' + activeKeys[index])" in template
    assert 'white-space: normal !important' in template
    assert 'overflow-wrap: anywhere !important' in template
    assert '.field-name' in template
    assert '.field-org' in template
    assert 'width: 200px' not in template
    assert 'width: 220px' not in template
    assert 'width: 240px' not in template
