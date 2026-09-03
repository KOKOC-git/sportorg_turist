from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sportorg.language import translate


class TourismTimeEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInputMask("99:99:99;_")
        self.setPlaceholderText("HH:MM:SS")

    def text(self):
        value = super().text()
        # Если пользователь ничего не ввёл, QLineEdit с маской возвращает "__:__:__".
        # Для расчёта это должно считаться пустым значением.
        if not value or value.replace(":", "").replace("_", "").strip() == "":
            return ""
        return value


from sportorg.gui.dialogs.tourism_time_edit import TourismTimeEdit
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.tourism import (
    CompetitionType,
    TourismJudgingMode,
    ensure_tourism_defaults, repair_tourism_data, repair_tourism_courses_from_stages,
    get_tourism_stages_for_group,
    hms_to_sec,
    is_tourism_competition_type,
    sec_to_hms,
)
from sportorg.services.tourism_result_calculation import TourismResultCalculator
from sportorg.services.tourism_decision_updates import (
    build_updated_tourism_decisions,
)


class TourismPenaltiesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Assign penalties / cutoff'))
        self.resize(1050, 700)

        ensure_tourism_defaults(race())
        repair_tourism_data(race())
        repair_tourism_courses_from_stages(race())
        repair_tourism_courses_from_stages(race())

        self.current_person = None
        self.stage_ids = []

        self.layout = QVBoxLayout(self)

        self._build_search_block()
        self._build_stage_table()
        self._build_bottom_buttons()

        self.btn_find.clicked.connect(self.find_competitor)
        self.btn_save.clicked.connect(self.save_all_decisions)
        self.btn_clear.clicked.connect(self.clear_for_current_person)
        self.btn_close.clicked.connect(self.accept)

        self.find_competitor()
        self.recalc_results()

    def _build_search_block(self):
        search_widget = QWidget(self)
        search_layout = QFormLayout(search_widget)

        self.person_bib = QLineEdit()
        self.person_name = QLineEdit()
        self.person_info = QLabel('')

        search_layout.addRow(translate('Bib'), self.person_bib)
        search_layout.addRow(translate('Surname'), self.person_name)
        search_layout.addRow(translate('Competitor'), self.person_info)

        self.layout.addWidget(search_widget)

        btn_row = QHBoxLayout()
        self.btn_find = QPushButton(translate('Find competitor'))
        btn_row.addWidget(self.btn_find)
        btn_row.addStretch(1)
        self.layout.addLayout(btn_row)

    def _build_stage_table(self):
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            translate('Stage'),
            translate('Penalty time'),
            translate('Penalty points'),
            translate('Cutoff'),
            translate('Stage DSQ'),
            translate('Comment'),
        ])
        self.layout.addWidget(self.table)

        hint = QLabel(
            'Заполните санкции по этапам. '
            'Если строка пустая — решение по этому этапу не сохраняется. '
            'Отсечку можно указывать и в режиме «Без штрафа».'
        )
        hint.setWordWrap(True)
        self.layout.addWidget(hint)

    def _build_bottom_buttons(self):
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton(translate('Save'))
        self.btn_clear = QPushButton('Очистить решения участника')
        self.btn_close = QPushButton(translate('Close'))

        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_close)

        self.layout.addLayout(btn_row)

    def _find_person(self):
        obj = race()
        bib = self.person_bib.text().strip()
        name = self.person_name.text().strip().lower()

        if not bib and not name:
            return None

        for person in obj.persons:
            if bib and str(getattr(person, 'bib', '')).strip() == bib:
                return person

        for person in obj.persons:
            full_name = str(getattr(person, 'full_name', '') or '').lower()
            simple_name = str(getattr(person, 'name', '') or '').lower()
            surname = str(getattr(person, 'surname', '') or '').lower()

            if name and (
                name in full_name
                or name in simple_name
                or name in surname
            ):
                return person

        return None

    def _is_tourism_person(self, person):
        if not person or not person.group:
            return False

        group_type = (
            person.group.get_competition_type()
            if hasattr(person.group, 'get_competition_type')
            else getattr(person.group, 'competition_type', None)
        )

        if not group_type:
            group_type = getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value)

        return is_tourism_competition_type(group_type)

    def find_competitor(self):
        self.current_person = self._find_person()

        if not self.current_person:
            self.person_info.setText('Участник не найден')
            self.load_empty_table()
            return

        person = self.current_person

        if not self._is_tourism_person(person):
            self.person_info.setText('Участник найден, но его группа не относится к виду «Туризм»')
            self.load_empty_table()
            return

        group_name = person.group.name if person.group else ''
        self.person_info.setText(f'{person.full_name} | группа: {group_name}')

        self.load_stage_table()

    def load_empty_table(self):
        self.stage_ids = []
        self.table.setRowCount(0)

    def _find_existing_decision(self, stage_id, person_id):
        for decision in getattr(race(), 'tourism_stage_decisions', []):
            if (
                str(decision.stage_id) == str(stage_id)
                and str(decision.person_id) == str(person_id)
            ):
                return decision
        return None

    def load_stage_table(self):
        person = self.current_person
        if not person or not person.group:
            self.load_empty_table()
            return

        stages = get_tourism_stages_for_group(race(), str(person.group.id))

        self.stage_ids = [str(stage.id) for stage in stages]
        self.table.setRowCount(len(stages))

        person_id = str(person.id)
        mode = getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value)
        is_penalty_mode = mode == TourismJudgingMode.PENALTY.value

        for row, stage in enumerate(stages):
            decision = self._find_existing_decision(stage.id, person_id)

            stage_item = QTableWidgetItem(f'{stage.order_num}. {stage.name}')
            stage_item.setFlags(stage_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, stage_item)

            penalty_time = TourismTimeEdit()
            penalty_time.setEnabled(is_penalty_mode)

            penalty_points = QLineEdit()
            penalty_points.setPlaceholderText('0')
            penalty_points.setEnabled(is_penalty_mode)

            cutoff_time = TourismTimeEdit()

            stage_dsq = QCheckBox()

            comment = QTextEdit()
            comment.setFixedHeight(45)

            if decision:
                if decision.penalty_time_sec:
                    penalty_time.setText(sec_to_hms(decision.penalty_time_sec))
                if decision.penalty_points:
                    penalty_points.setText(str(decision.penalty_points))
                if decision.cutoff_time_sec:
                    cutoff_time.setText(sec_to_hms(decision.cutoff_time_sec))
                stage_dsq.setChecked(bool(decision.is_stage_dsq))
                comment.setPlainText(decision.comment or '')

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

            self.table.setCellWidget(row, 1, penalty_time)
            self.table.setCellWidget(row, 2, penalty_points)
            self.table.setCellWidget(row, 3, cutoff_time)
            self.table.setCellWidget(row, 4, stage_dsq)
            self.table.setCellWidget(row, 5, comment)

        self.table.resizeColumnsToContents()

    def _row_values(self, row):
        penalty_time_widget = self.table.cellWidget(row, 1)
        penalty_points_widget = self.table.cellWidget(row, 2)
        cutoff_widget = self.table.cellWidget(row, 3)
        dsq_widget = self.table.cellWidget(row, 4)
        comment_widget = self.table.cellWidget(row, 5)

        penalty_time_text = penalty_time_widget.text().strip() if penalty_time_widget else ''
        penalty_points_text = penalty_points_widget.text().strip() if penalty_points_widget else ''
        cutoff_text = cutoff_widget.text().strip() if cutoff_widget else ''
        is_dsq = dsq_widget.isChecked() if dsq_widget else False
        comment = comment_widget.toPlainText().strip() if comment_widget else ''

        penalty_time_sec = hms_to_sec(penalty_time_text)
        penalty_points = int(penalty_points_text or '0')
        cutoff_time_sec = hms_to_sec(cutoff_text)

        return penalty_time_sec, penalty_points, cutoff_time_sec, is_dsq, comment

    def save_all_decisions(self):
        person = self.current_person
        if not person:
            QMessageBox.warning(self, translate('Error'), translate('Competitor not found'))
            return

        if not self._is_tourism_person(person):
            QMessageBox.warning(self, translate('Error'), translate('Competitor group is not configured as Tourism'))
            return

        person_id = str(person.id)
        mode = TourismJudgingMode(
            getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value)
        )

        try:
            updates = []
            for row, stage_id in enumerate(self.stage_ids):
                penalty_time_sec, penalty_points, cutoff_time_sec, is_dsq, comment = self._row_values(row)
                updates.append({
                    'stage_id': str(stage_id),
                    'person_id': person_id,
                    'penalty_time_sec': penalty_time_sec,
                    'penalty_points': penalty_points,
                    'cutoff_time_sec': cutoff_time_sec,
                    'is_stage_dsq': is_dsq,
                    'comment': comment,
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
        self.load_stage_table()
        QMessageBox.information(self, translate('Save'), 'Штрафы и отсечки сохранены')

    def clear_for_current_person(self):
        person = self.current_person
        if not person:
            return

        person_id = str(person.id)
        race().tourism_stage_decisions = [
            d for d in race().tourism_stage_decisions
            if str(d.person_id) != person_id
        ]

        self.recalc_results()
        self.load_stage_table()

    def recalc_results(self):
        TourismResultCalculator.apply(race())
        ResultCalculation(race()).process_results()
