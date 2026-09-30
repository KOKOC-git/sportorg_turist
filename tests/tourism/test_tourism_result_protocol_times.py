import shutil
import subprocess
from pathlib import Path

import pytest


TEMPLATE = (
    Path(__file__).parents[2] / 'templates' / 'reports' / 'tourism' / 'results.html'
)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is unavailable')
def test_protocol_separates_elapsed_time_from_adjusted_result():
    source = TEMPLATE.read_text(encoding='utf-8')
    formatters = source[
        source.index('    function toHHMMSSFromMsec('):
        source.index('    function getTourismStagesSorted(')
    ]
    result_helpers = source[
        source.index('    function getResultMsec('):
        source.index('    function getPenaltyText(')
    ]
    script = formatters + result_helpers + """
        const result = {
            start_time: 36000000,
            start_msec: 36000000,
            finish_time: 37800000,
            result_current: '00:31:30'
        };
        if (getElapsedTimeText(result) !== '00:30:00') process.exit(1);
        if (getResultText(result) !== '00:31:30') process.exit(2);
        const planned = {
            start_time: null,
            start_msec: 36000000,
            finish_time: 37800000,
            person: {start_time: 36000000}
        };
        if (getStartTimeText(planned) !== '10:00:00') process.exit(3);
        if (getElapsedTimeText(planned) !== '00:30:00') process.exit(4);
        if (getElapsedTimeText({start_time: null, finish_time: 37800000}) !== '') process.exit(5);
    """

    subprocess.run(['node', '-e', script], check=True)
    assert "'Время прохождения'" in source
    assert "['Штраф', 'Результат', 'Статус', 'Очки']" in source


def test_group_protocol_combines_members_and_uses_last_finish():
    source = TEMPLATE.read_text(encoding='utf-8')

    assert "race.competition_type === 'tourism_group'" in source
    assert 'function buildTourismGroupResults()' in source
    assert 'Number(b.finish_time || 0) - Number(a.finish_time || 0)' in source
    assert "filter(Boolean).join('; ')" in source
    assert "'Состав группы'" in source
    assert 'function createTeamMembersCell(result)' in source
    assert 'var splitAt = Math.ceil(names.length / 2)' in source
    assert "table.classList.add('tourism-group-results')" in source
    assert 'white-space: nowrap !important' in source
    assert 'word-break: keep-all !important' in source
    assert 'function createTeamCell(result)' in source
    assert 'splitTextIntoBalancedLines(getTeamName(result), 3)' in source
    assert "return orientation === 'landscape' ? 5 : 3" in source
    assert "printPageSize.addEventListener('change', rerenderForPageFormat)" in source
