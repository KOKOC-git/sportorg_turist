import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
)

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvSpinBox
from sportorg.language import translate
from sportorg.models.memory import race


class TourismStandingsSettingsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Tourism standings settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(False)
        self.setMinimumWidth(720)

        self.layout = QFormLayout(self)
        obj = race()

        self.hint = QLabel(translate('Tourism standings settings hint'))
        self.hint.setWordWrap(True)
        self.layout.addRow(self.hint)

        self.count_scores = AdvSpinBox(minimum=0, maximum=999, value=0)
        self.count_scores.setValue(
            int(obj.get_setting('tourism_standings_count_scores', 0) or 0)
        )
        self.layout.addRow(
            translate('Counted results quantity'),
            self.count_scores,
        )

        self.min_female_count = AdvSpinBox(minimum=0, maximum=999, value=0)
        self.min_female_count.setValue(
            int(obj.get_setting('tourism_standings_min_female_count', 0) or 0)
        )
        self.layout.addRow(
            translate('Minimum female results quantity'),
            self.min_female_count,
        )

        self.female_prefix = QLineEdit()
        self.female_prefix.setText(
            str(obj.get_setting('tourism_standings_female_group_prefix', 'Ж') or 'Ж')
        )
        self.layout.addRow(
            translate('Female group prefix'),
            self.female_prefix,
        )

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(apply_changes)

        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)

        self.layout.addRow(button_box)
        self.show()

    def apply_changes_impl(self):
        obj = race()
        obj.set_setting(
            'tourism_standings_count_scores',
            self.count_scores.value(),
        )
        obj.set_setting(
            'tourism_standings_min_female_count',
            self.min_female_count.value(),
        )
        obj.set_setting(
            'tourism_standings_female_group_prefix',
            self.female_prefix.text().strip() or 'Ж',
        )
