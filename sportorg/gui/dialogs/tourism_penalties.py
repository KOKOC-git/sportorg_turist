from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.tourism import (
    CompetitionType,
    TourismJudgingMode,
    TourismStageDecision,
    ensure_tourism_defaults,
    get_tourism_stages_for_group,
    hms_to_sec,
    sec_to_hms,
)
from sportorg.services.tourism_result_calculation import TourismResultCalculator


class TourismPenaltiesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Assign penalties / cutoff'))
        self.resize(980, 680)

        ensure_tourism_defaults(race())

        self.layout = QVBoxLayout(self)

        self.top_form = QFormLayout()

        self.person_bib = QLineEdit()
        self.person_name = QLineEdit()
        self.person_group = QLabel('')
        self.stage_combo = QComboBox()

        self.top_form.addRow(translate('Bib'), self.person_bib)
        self.top_form.addRow(translate('Surname'), self.person_name)
        self.top_form.addRow(translate('Group'), self.person_group)
        self.top_form.addRow(translate('Stage'), self.stage_combo)

        self.layout.addLayout(self.top_form)

        sanctions_widget = QWidget()
        sanctions_layout = QFormLayout(sanctions_widget)

        self.penalty_time = QLineEdit()
        self.penalty_time.setPlaceholderText('HH:MM:SS')
        self.penalty_points = QLineEdit()
        self.penalty_points.setPlaceholderText('0')
        self.cutoff_time = QLineEdit()
        self.cutoff_time.setPlaceholderText('HH:MM:SS')
        self.stage_dsq = QCheckBox(translate('Stage DSQ'))
        self.comment = QTextEdit()
        self.comment.setFixedHeight(90)

        sanctions_layout.addRow(translate('Penalty time'), self.penalty_time)
        sanctions_layout.addRow(translate('Penalty points'), self.penalty_points)
        sanctions_layout.addRow(translate('Cutoff'), self.cutoff_time)
        sanctions_layout.addRow('', self.stage_dsq)
        sanctions_layout.addRow(translate('Comment'), self.comment)

        self.layout.addWidget(sanctions_widget)

        btn_row = QHBoxLayout()
        self.btn_find = QPushButton(translate('Find competitor'))
        self.btn_save = QPushButton(translate('Save'))
        self.btn_delete = QPushButton(translate('Delete selected'))
        self.btn_close = QPushButton(translate('Close'))
        btn_row.addWidget(self.btn_find)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_delete)
        btn_row.addWidget(self.btn_close)
        self.layout.addLayout(btn_row)

        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            translate('Bib'),
            translate('Name'),
            translate('Group'),
            translate('Stage'),
            translate('Penalty time'),
            translate('Penalty points'),
            translate('Cutoff'),
            translate('Stage DSQ'),
        ])
        self.layout.addWidget(self.table)

        self.stage_dsq.stateChanged.connect(self.on_stage_dsq_changed)
        self.btn_find.clicked.connect(self.sync_competitor_and_stages)
        self.btn_save.clicked.connect(self.save_decision)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_close.clicked.connect(self.accept)

        self._apply_judging_mode()
        self.sync_competitor_and_stages()
        self.recalc_results()
        self.reload_table()

    def _apply_judging_mode(self):
        mode = getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value)
        is_penalty_mode = mode == TourismJudgingMode.PENALTY.value
        self.penalty_time.setVisible(is_penalty_mode)
        self.penalty_points.setVisible(is_penalty_mode)
        self.penalty_time.setEnabled(is_penalty_mode and not self.stage_dsq.isChecked())
        self.penalty_points.setEnabled(is_penalty_mode and not self.stage_dsq.isChecked())

    def on_stage_dsq_changed(self):
        is_penalty_mode = getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value) == TourismJudgingMode.PENALTY.value
        self.penalty_time.setEnabled(is_penalty_mode and not self.stage_dsq.isChecked())
        self.penalty_points.setEnabled(is_penalty_mode and not self.stage_dsq.isChecked())
        if self.stage_dsq.isChecked():
            self.penalty_time.setText('')
            self.penalty_points.setText('')

    def _find_person(self):
        obj = race()
        bib = self.person_bib.text().strip()
        name = self.person_name.text().strip().lower()
        for person in obj.persons:
            if bib and str(getattr(person, 'bib', '')).strip() == bib:
                return person
            if name and name in str(getattr(person, 'name', '')).lower():
                return person
        return None

    def sync_competitor_and_stages(self):
        self.stage_combo.clear()
        person = self._find_person()
        if not person or not person.group:
            self.person_group.setText('')
            return

        group_type = person.group.get_competition_type() if hasattr(person.group, 'get_competition_type') else getattr(person.group, 'competition_type', None) or getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value)
        self.person_group.setText(person.group.name)
        if group_type != CompetitionType.TOURISM.value:
            return

        stages = get_tourism_stages_for_group(race(), str(person.group.id))
        for stage in stages:
            self.stage_combo.addItem(f'{stage.order_num}. {stage.name}', stage.id)

    def _get_current_stage_id(self):
        return self.stage_combo.currentData()

    def _find_stage_name(self, stage_id):
        for stage in race().tourism_stages:
            if stage.id == stage_id:
                return stage.name
        return ''

    def _get_decisions_for_current_group(self):
        person = self._find_person()
        if not person:
            return []
        return [d for d in race().tourism_stage_decisions if d.person_id == str(person.id)]

    def _find_existing_decision(self, stage_id: str, person_id: str):
        for d in race().tourism_stage_decisions:
            if d.stage_id == stage_id and d.person_id == person_id:
                return d
        return None

    def recalc_results(self):
        TourismResultCalculator.apply(race())
        ResultCalculation(race()).process_results()

    def save_decision(self):
        person = self._find_person()
        if not person:
            QMessageBox.warning(self, translate('Error'), translate('Competitor not found'))
            return

        if hasattr(person.group, 'get_competition_type') and person.group.get_competition_type() != CompetitionType.TOURISM.value:
            QMessageBox.warning(self, translate('Error'), translate('Competitor group is not configured as Tourism'))
            return

        stage_id = self._get_current_stage_id()
        if not stage_id:
            QMessageBox.warning(self, translate('Error'), translate('No stages configured for competitor group'))
            return

        mode = TourismJudgingMode(getattr(race(), 'tourism_judging_mode', TourismJudgingMode.PENALTY.value))
        existing = self._find_existing_decision(stage_id, str(person.id))
        decision = existing or TourismStageDecision(stage_id=stage_id, person_id=str(person.id))

        try:
            decision.penalty_time_sec = hms_to_sec(self.penalty_time.text())
            decision.penalty_points = int(self.penalty_points.text() or '0')
            decision.cutoff_time_sec = hms_to_sec(self.cutoff_time.text())
            decision.is_stage_dsq = self.stage_dsq.isChecked()
            decision.comment = self.comment.toPlainText().strip()
            decision.updated_at = datetime.utcnow().isoformat()
            decision.validate(mode)
        except Exception as e:
            QMessageBox.warning(self, translate('Error'), str(e))
            return

        if existing is None:
            race().tourism_stage_decisions.append(decision)

        self.recalc_results()
        self.reload_table()
        self.clear_form()

    def clear_form(self):
        self.penalty_time.setText('')
        self.penalty_points.setText('')
        self.cutoff_time.setText('')
        self.stage_dsq.setChecked(False)
        self.comment.setPlainText('')

    def reload_table(self):
        decisions = race().tourism_stage_decisions
        self.table.setRowCount(len(decisions))
        person_map = {str(p.id): p for p in race().persons}
        for row, d in enumerate(decisions):
            person = person_map.get(d.person_id)
            bib = str(getattr(person, 'bib', '')) if person else ''
            name = str(getattr(person, 'name', '')) if person else ''
            group_name = person.group.name if person and person.group else ''
            stage_name = self._find_stage_name(d.stage_id)
            self.table.setItem(row, 0, QTableWidgetItem(bib))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(group_name))
            self.table.setItem(row, 3, QTableWidgetItem(stage_name))
            self.table.setItem(row, 4, QTableWidgetItem(sec_to_hms(d.penalty_time_sec)))
            self.table.setItem(row, 5, QTableWidgetItem(str(d.penalty_points)))
            self.table.setItem(row, 6, QTableWidgetItem(sec_to_hms(d.cutoff_time_sec)))
            self.table.setItem(row, 7, QTableWidgetItem(translate('Yes') if d.is_stage_dsq else ''))
            self.table.item(row, 0).setData(Qt.UserRole, d.id)

    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is None:
            return
        decision_id = item.data(Qt.UserRole)
        race().tourism_stage_decisions = [d for d in race().tourism_stage_decisions if d.id != decision_id]
        self.recalc_results()
        self.reload_table()
