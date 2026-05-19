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
from sportorg.models.memory import race


class TourismTeamMembersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Tourism team members'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setMinimumSize(850, 500)

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            translate('Tourism team'),
            translate('Tourism team leg'),
            translate('Bib'),
            translate('Name'),
            translate('Group'),
            translate('Team'),
        ])
        self.layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setText(translate('Close'))
        button_box.rejected.connect(self.close)
        self.layout.addWidget(button_box)

        self.load_data()

    def load_data(self):
        persons = [
            person for person in race().persons
            if int(getattr(person, 'tourism_team_number', 0) or 0) > 0
        ]

        persons.sort(
            key=lambda p: (
                int(getattr(p, 'tourism_team_number', 0) or 0),
                int(getattr(p, 'tourism_team_leg', 0) or 0),
                int(getattr(p, 'bib', 0) or 0),
                p.full_name,
            )
        )

        self.table.setRowCount(len(persons))

        for row, person in enumerate(persons):
            group_name = person.group.name if person.group else ''
            team_name = person.organization.name if person.organization else ''

            values = [
                getattr(person, 'tourism_team_number', 0) or '',
                getattr(person, 'tourism_team_leg', 0) or '',
                getattr(person, 'bib', '') or '',
                person.full_name,
                group_name,
                team_name,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
