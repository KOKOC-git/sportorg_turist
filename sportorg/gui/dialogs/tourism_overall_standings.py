from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from sportorg import config
from sportorg.language import translate
from sportorg.services.tourism_overall_standings import build_tourism_overall_standings


class TourismOverallStandingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Tourism overall standings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setMinimumSize(1100, 550)

        self.rows = []

        self.layout = QVBoxLayout(self)

        self.filter_layout = QHBoxLayout()
        self.filter_layout.addWidget(QLabel(translate('Age group')))

        self.group_filter = QComboBox()
        self.group_filter.currentTextChanged.connect(self.apply_filter)
        self.filter_layout.addWidget(self.group_filter)

        self.filter_layout.addStretch()
        self.layout.addLayout(self.filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            translate('Age group'),
            translate('Place'),
            translate('Team'),
            translate('Scores'),
            translate('Count'),
            translate('Details'),
        ])
        self.layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setText(translate('Close'))
        button_box.rejected.connect(self.close)
        self.layout.addWidget(button_box)

        self.load_data()

    def load_data(self):
        self.rows = build_tourism_overall_standings()

        group_names = sorted(
            {
                str(getattr(row, 'group_name', '') or translate('Without group'))
                for row in self.rows
            },
            key=lambda value: value.lower(),
        )

        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem(translate('All age groups'))
        self.group_filter.addItems(group_names)
        self.group_filter.blockSignals(False)

        self.apply_filter()

    def apply_filter(self):
        selected_group = self.group_filter.currentText()

        if selected_group == translate('All age groups'):
            rows = self.rows
        else:
            rows = [
                row for row in self.rows
                if str(getattr(row, 'group_name', '') or translate('Without group')) == selected_group
            ]

        self.render_rows(rows)

    def render_rows(self, rows):
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.group_name,
                row.place,
                row.team_name,
                row.scores,
                row.unit_count,
                row.details,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_index, col, item)

        self.table.resizeColumnsToContents()
