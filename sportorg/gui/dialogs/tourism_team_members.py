from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
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

        self.button_delete_team = button_box.addButton(
            translate('Delete tourism team'),
            QDialogButtonBox.ActionRole,
        )
        self.button_delete_team.clicked.connect(self.delete_selected_team)

        button_box.rejected.connect(self.close)
        self.layout.addWidget(button_box)

        self.load_data()

    def delete_selected_team(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                translate('Information'),
                translate('Select tourism team to delete'),
            )
            return

        team_item = self.table.item(row, 0)
        if team_item is None:
            return

        try:
            team_number = int(team_item.text())
        except Exception:
            QMessageBox.warning(
                self,
                translate('Error'),
                translate('Incorrect tourism team number'),
            )
            return

        answer = QMessageBox.question(
            self,
            translate('Delete'),
            translate('Delete selected tourism team') + f' №{team_number}?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        changed = 0
        for person in race().persons:
            if int(getattr(person, 'tourism_team_number', 0) or 0) == team_number:
                person.tourism_team_number = 0
                person.tourism_team_leg = 0
                changed += 1

        self.load_data()

        try:
            from sportorg.gui.global_access import GlobalAccess
            GlobalAccess().get_main_window().refresh()
        except Exception:
            pass

        QMessageBox.information(
            self,
            translate('Information'),
            translate('Tourism team deleted') + f': {changed}',
        )

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
