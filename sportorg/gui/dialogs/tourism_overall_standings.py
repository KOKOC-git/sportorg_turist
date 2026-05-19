from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
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
        rows = build_tourism_overall_standings()
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
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
