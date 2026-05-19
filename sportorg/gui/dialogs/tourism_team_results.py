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
from sportorg.services.tourism_team_units import build_tourism_team_units


class TourismTeamResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Tourism team results'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setMinimumSize(1100, 550)

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            translate('Tourism team'),
            translate('Bib'),
            translate('Name'),
            translate('Group'),
            translate('Team'),
            translate('Result bib'),
            translate('Result'),
            translate('Scores'),
            translate('Warning'),
        ])
        self.layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setText(translate('Close'))
        button_box.rejected.connect(self.close)
        self.layout.addWidget(button_box)

        self.load_data()

    def load_data(self):
        units = build_tourism_team_units()
        self.table.setRowCount(len(units))

        for row, unit in enumerate(units):
            values = [
                unit.number,
                unit.bibs_text,
                unit.members_text,
                unit.group_name,
                unit.team_name,
                unit.result_bib,
                unit.result_text,
                unit.scores,
                translate(unit.warning_text) if unit.warning_text else '',
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
