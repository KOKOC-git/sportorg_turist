from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from sportorg.language import translate
from sportorg.gui.dialogs.tourism_time_edit import TourismTimeEdit
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.tourism import (
    CompetitionType,
    TourismJudgingMode,
    ensure_tourism_defaults, repair_tourism_data, repair_tourism_courses_from_stages,
    hms_to_sec,
    is_tourism_competition_type,
    sec_to_hms,
)
from sportorg.services.tourism_result_calculation import TourismResultCalculator
from sportorg.services.tourism_decision_updates import (
    build_updated_tourism_decisions,
)


class TourismStagePenaltiesDialog(QDialog):
    """
    Массовый ввод санкций по одному этапу:
    один этап -> список участников -> штрафы / отсечки / снятия.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Штрафы / отсечки по этапу')
        self.resize(1200, 720)

        ensure_tourism_defaults(race())
        repair_tourism_data(race())
        repair_tourism_courses_from_stages(race())
        repair_tourism_courses_from_stages(race())

        self.stage_ids = []
        self.person_ids = []

        self.layout = QVBoxLayout(self)

        self._build_top()
        self._build_table()
        self._build_buttons()

        self.stage_combo.currentIndexChanged.connect(self.load_stage_persons)
        self.btn_save.clicked.connect(self.save_all)
        self.btn_clear_stage.clicked.connect(self.clear_stage_decisions)
        self.btn_close.clicked.connect(self.accept)

        self.load_stages()
        self.load_stage_persons()

    def _build_top(self):
        top = QHBoxLayout()

        top.addWidget(QLabel('Этап'))
        self.stage_combo = QComboBox()
        top.addWidget(self.stage_combo, 1)

        self.info_label = QLabel('')
        top.addWidget(self.info_label)

        self.layout.addLayout(top)

        hint = QLabel(
            'Выберите этап и заполните санкции для нужных участников. '
            'Пустые строки не сохраняются. Если строку очистить — ранее сохранённое решение по этому этапу удалится.'
        )
        hint.setWordWrap(True)
        self.layout.addWidget(hint)

    def _build_table(self):
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            '№',
            'Участник',
            'Группа',
            'Команда',
            'Штраф временем',
            'Штраф баллами',
            'Отсечка',
            'Снятие с этапа',
        ])
        self.layout.addWidget(self.table)

    def _build_buttons(self):
        row = QHBoxLayout()

        self.btn_save = QPushButton(translate('Save'))
        self.btn_clear_stage = QPushButton('Очистить решения по этапу')
        self.btn_close = QPushButton(translate('Close'))

        row.addStretch(1)
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_clear_stage)
        row.addWidget(self.btn_close)

        self.layout.addLayout(row)

    def _is_tourism_group(self, group):
        if not group:
            return False

        if hasattr(group, 'get_competition_type'):
            group_type = group.get_competition_type()
        else:
            group_type = getattr(group, 'competition_type', None)

        if not group_type:
            group_type = getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value)

        return is_tourism_competition_type(group_type)

    def _stage_course_id(self, stage):
        return str(getattr(stage, 'tourism_course_id', '') or '')

    def _course_group_ids(self, course_id):
        if not course_id:
            return []

        for tourism_course in getattr(race(), 'tourism_courses', []):
            if str(getattr(tourism_course, 'id', '')) == str(course_id):
                return [str(x) for x in getattr(tourism_course, 'group_ids', [])]

        return []

    def _person_team_name(self, person):
        org = getattr(person, 'organization', None)
        if not org:
            return ''
        return getattr(org, 'name', '') or ''

    def load_stages(self):
        self.stage_combo.clear()
        self.stage_ids = []

        stages = sorted(
            getattr(race(), 'tourism_stages', []),
            key=lambda x: (
                str(getattr(x, 'tourism_course_id', '') or ''),
                int(getattr(x, 'order_num', 0) or 0),
                str(getattr(x, 'name', '') or ''),
            ),
        )

        for stage in stages:
            course_name = ''
            course_id = self._stage_course_id(stage)

            for tourism_course in getattr(race(), 'tourism_courses', []):
                if str(getattr(tourism_course, 'id', '')) == course_id:
                    course_name = getattr(tourism_course, 'name', '') or ''
                    break

            title = f'{stage.order_num}. {stage.name}'
            if course_name:
                title = f'{course_name} — {title}'

            self.stage_combo.addItem(title, str(stage.id))
            self.stage_ids.append(str(stage.id))

    def _current_stage(self):
        stage_id = self.stage_combo.currentData()
        if not stage_id:
            return None

        for stage in getattr(race(), 'tourism_stages', []):
            if str(stage.id) == str(stage_id):
                return stage

        return None

    def _stage_persons(self, stage):
        if not stage:
            return []

        course_id = self._stage_course_id(stage)
        group_ids = self._course_group_ids(course_id)

        persons = []

        for person in getattr(race(), 'persons', []):
            group = getattr(person, 'group', None)
            if not group:
                continue

            if not self._is_tourism_group(group):
                continue

            if group_ids and str(group.id) not in group_ids:
                continue

            persons.append(person)

        persons.sort(
            key=lambda p: (
                str(getattr(p.group, 'name', '') if getattr(p, 'group', None) else ''),
                int(getattr(p, 'bib', 0) or 0),
                str(getattr(p, 'full_name', '') or ''),
            )
        )

        return persons

    def _find_decision(self, stage_id, person_id):
        for decision in getattr(race(), 'tourism_stage_decisions', []):
            if (
                str(decision.stage_id) == str(stage_id)
                and str(decision.person_id) == str(person_id)
            ):
                return decision

        return None

    def load_stage_persons(self):
        stage = self._current_stage()

        if not stage:
            self.person_ids = []
            self.table.setRowCount(0)
            self.info_label.setText('Этап не выбран')
            return

        persons = self._stage_persons(stage)
        self.person_ids = [str(person.id) for person in persons]

        self.table.setRowCount(len(persons))

        mode = getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value)
        is_penalty_mode = mode == TourismJudgingMode.PENALTY.value

        stage_id = str(stage.id)

        for row, person in enumerate(persons):
            person_id = str(person.id)
            decision = self._find_decision(stage_id, person_id)

            bib_item = QTableWidgetItem(str(getattr(person, 'bib', '') or ''))
            name_item = QTableWidgetItem(str(getattr(person, 'full_name', '') or ''))
            group_item = QTableWidgetItem(str(getattr(person.group, 'name', '') if person.group else ''))
            team_item = QTableWidgetItem(self._person_team_name(person))

            for item in (bib_item, name_item, group_item, team_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row, 0, bib_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, group_item)
            self.table.setItem(row, 3, team_item)

            penalty_time = TourismTimeEdit()
            penalty_time.setPlaceholderText('HH:MM:SS')
            penalty_time.setEnabled(is_penalty_mode)

            penalty_points = QLineEdit()
            penalty_points.setPlaceholderText('0')
            penalty_points.setEnabled(is_penalty_mode)

            cutoff_time = TourismTimeEdit()
            cutoff_time.setPlaceholderText('HH:MM:SS')

            stage_dsq = QCheckBox()

            if decision:
                if int(getattr(decision, 'penalty_time_sec', 0) or 0):
                    penalty_time.setText(sec_to_hms(decision.penalty_time_sec))
                if int(getattr(decision, 'penalty_points', 0) or 0):
                    penalty_points.setText(str(decision.penalty_points))
                if int(getattr(decision, 'cutoff_time_sec', 0) or 0):
                    cutoff_time.setText(sec_to_hms(decision.cutoff_time_sec))
                stage_dsq.setChecked(bool(getattr(decision, 'is_stage_dsq', False)))

            def make_dsq_handler(pt, pp, dsq):
                def handler():
                    checked = dsq.isChecked()
                    pt.setEnabled(is_penalty_mode and not checked)
                    pp.setEnabled(is_penalty_mode and not checked)
                    if checked:
                        pt.setText('')
                        pp.setText('')
                return handler

            stage_dsq.stateChanged.connect(
                make_dsq_handler(penalty_time, penalty_points, stage_dsq)
            )
            make_dsq_handler(penalty_time, penalty_points, stage_dsq)()

            self.table.setCellWidget(row, 4, penalty_time)
            self.table.setCellWidget(row, 5, penalty_points)
            self.table.setCellWidget(row, 6, cutoff_time)
            self.table.setCellWidget(row, 7, stage_dsq)

        self.info_label.setText(f'Участников: {len(persons)}')
        self.table.resizeColumnsToContents()

    def _row_values(self, row):
        penalty_time_widget = self.table.cellWidget(row, 4)
        penalty_points_widget = self.table.cellWidget(row, 5)
        cutoff_widget = self.table.cellWidget(row, 6)
        dsq_widget = self.table.cellWidget(row, 7)

        penalty_time_text = penalty_time_widget.text().strip() if penalty_time_widget else ''
        penalty_points_text = penalty_points_widget.text().strip() if penalty_points_widget else ''
        cutoff_text = cutoff_widget.text().strip() if cutoff_widget else ''
        is_dsq = dsq_widget.isChecked() if dsq_widget else False

        return (
            hms_to_sec(penalty_time_text),
            int(penalty_points_text or '0'),
            hms_to_sec(cutoff_text),
            is_dsq,
        )

    def save_all(self):
        stage = self._current_stage()
        if not stage:
            QMessageBox.warning(self, translate('Error'), 'Этап не выбран')
            return

        stage_id = str(stage.id)

        mode = TourismJudgingMode(
            getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value)
        )

        try:
            updates = []
            for row, person_id in enumerate(self.person_ids):
                penalty_time_sec, penalty_points, cutoff_time_sec, is_dsq = self._row_values(row)
                updates.append({
                    'stage_id': stage_id,
                    'person_id': person_id,
                    'penalty_time_sec': penalty_time_sec,
                    'penalty_points': penalty_points,
                    'cutoff_time_sec': cutoff_time_sec,
                    'is_stage_dsq': is_dsq,
                })

            updated_decisions = build_updated_tourism_decisions(
                race().tourism_stage_decisions,
                updates,
                mode,
            )

        except Exception as e:
            QMessageBox.warning(self, translate('Error'), str(e))
            return

        race().tourism_stage_decisions = updated_decisions

        self.recalc_results()
        self.load_stage_persons()
        QMessageBox.information(self, translate('Save'), 'Санкции по этапу сохранены')

    def clear_stage_decisions(self):
        stage = self._current_stage()
        if not stage:
            return

        stage_id = str(stage.id)

        race().tourism_stage_decisions = [
            d for d in race().tourism_stage_decisions
            if str(d.stage_id) != stage_id
        ]

        self.recalc_results()
        self.load_stage_persons()

    def recalc_results(self):
        TourismResultCalculator.apply(race())
        ResultCalculation(race()).process_results()
