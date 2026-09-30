from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

import sportorg.gui.dialogs.tourism_stages as tourism_stages
from sportorg.models.tourism import TourismCourse


def test_tourism_event_shows_groups_with_stale_individual_type(monkeypatch):
    app = QApplication.instance() or QApplication([])
    group = SimpleNamespace(
        id='group-1',
        name='Мужчины',
        competition_type='individual',
        get_competition_type=lambda: 'individual',
    )
    old_course = TourismCourse(name='Старая дистанция', group_ids=['group-1'])
    new_course = TourismCourse(name='Новая дистанция')
    race_stub = SimpleNamespace(
        competition_type='tourism_group',
        groups=[group],
        courses=[],
        tourism_courses=[old_course, new_course],
        tourism_stages=[],
        tourism_stage_results=[],
    )
    monkeypatch.setattr(tourism_stages, 'race', lambda: race_stub)

    dialog = tourism_stages.TourismStagesDialog()
    index = dialog.course_combo.findData(new_course.id)
    dialog.course_combo.setCurrentIndex(index)

    assert 'group-1' in dialog.group_checkboxes
    assert old_course.group_ids == ['group-1']
    assert new_course.group_ids == []
    checkbox = dialog.group_checkboxes['group-1']
    assert 'сейчас: Старая дистанция' in checkbox.text()

    checkbox.setChecked(True)
    dialog.save_current_course()

    assert new_course.group_ids == ['group-1']
    assert old_course.group_ids == []
    dialog.close()
    assert app is not None
