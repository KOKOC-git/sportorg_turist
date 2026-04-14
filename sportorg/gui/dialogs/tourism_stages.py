from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.tourism import CompetitionType, TourismStage, ensure_tourism_defaults


class TourismStagesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Tourism stages'))
        self.resize(760, 500)

        ensure_tourism_defaults(race())

        self.layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.group_label = QLabel(translate('Group'))
        self.group_combo = QComboBox()
        top_row.addWidget(self.group_label)
        top_row.addWidget(self.group_combo, 1)
        self.layout.addLayout(top_row)

        self.info_label = QLabel(translate('Enter stages for the selected group in the order they are passed'))
        self.layout.addWidget(self.info_label)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([translate('Order'), translate('Stage name')])
        self.layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton(translate('Add stage'))
        self.btn_delete = QPushButton(translate('Delete stage'))
        self.btn_up = QPushButton(translate('Up'))
        self.btn_down = QPushButton(translate('Down'))
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_delete)
        btn_row.addWidget(self.btn_up)
        btn_row.addWidget(self.btn_down)
        self.layout.addLayout(btn_row)

        bottom_row = QHBoxLayout()
        self.btn_save = QPushButton(translate('Save'))
        self.btn_cancel = QPushButton(translate('Cancel'))
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.btn_save)
        bottom_row.addWidget(self.btn_cancel)
        self.layout.addLayout(bottom_row)

        self.btn_add.clicked.connect(self.add_stage)
        self.btn_delete.clicked.connect(self.delete_stage)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)
        self.group_combo.currentIndexChanged.connect(self.load_data)

        self.load_groups()
        self.load_data()

    def load_groups(self):
        self.group_combo.clear()
        for group in race().groups:
            group_type = getattr(group, 'get_competition_type', None)
            current_type = group.get_competition_type() if callable(group_type) else getattr(group, 'competition_type', None) or getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value)
            if current_type == CompetitionType.TOURISM.value:
                self.group_combo.addItem(group.name, str(group.id))

    def get_current_group_id(self):
        return self.group_combo.currentData()

    def get_group_stages(self):
        group_id = self.get_current_group_id()
        stages = [x for x in race().tourism_stages if x.group_id == group_id]
        return sorted(stages, key=lambda x: x.order_num)

    def load_data(self):
        stages = self.get_group_stages()
        self.table.setRowCount(len(stages))
        for row, stage in enumerate(stages):
            self.table.setItem(row, 0, QTableWidgetItem(str(stage.order_num)))
            self.table.setItem(row, 1, QTableWidgetItem(stage.name))

    def normalize_order_numbers(self):
        for row in range(self.table.rowCount()):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def add_stage(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(''))

    def delete_stage(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.table.removeRow(row)
        self.normalize_order_numbers()

    def move_up(self):
        row = self.table.currentRow()
        if row <= 0:
            return
        for col in range(self.table.columnCount()):
            upper = self.table.takeItem(row - 1, col)
            current = self.table.takeItem(row, col)
            self.table.setItem(row - 1, col, current)
            self.table.setItem(row, col, upper)
        self.table.setCurrentCell(row - 1, 0)
        self.normalize_order_numbers()

    def move_down(self):
        row = self.table.currentRow()
        if row < 0 or row >= self.table.rowCount() - 1:
            return
        for col in range(self.table.columnCount()):
            current = self.table.takeItem(row, col)
            lower = self.table.takeItem(row + 1, col)
            self.table.setItem(row, col, lower)
            self.table.setItem(row + 1, col, current)
        self.table.setCurrentCell(row + 1, 0)
        self.normalize_order_numbers()

    def save(self):
        group_id = self.get_current_group_id()
        if not group_id:
            QMessageBox.warning(self, translate('Error'), translate('Group is not selected'))
            return

        stages = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            name = name_item.text().strip() if name_item else ''
            if not name:
                QMessageBox.warning(self, translate('Error'), translate('Stage name cannot be empty'))
                return
            stages.append(TourismStage(group_id=group_id, order_num=row + 1, name=name))

        race().tourism_stages = [x for x in race().tourism_stages if x.group_id != group_id]
        race().tourism_stages.extend(stages)
        self.accept()
