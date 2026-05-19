import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.services.tourism_scores import DEFAULT_TOURISM_SCORES


class TourismScoresDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Tourism scores'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(False)
        self.setMinimumWidth(750)

        self.layout = QFormLayout(self)

        self.hint = QLabel(translate('Tourism scores hint'))
        self.hint.setWordWrap(True)
        self.layout.addRow(self.hint)

        obj = race()

        self.individual_scores = QLineEdit()
        self.individual_scores.setText(
            obj.get_setting('tourism_individual_scores_array', DEFAULT_TOURISM_SCORES)
        )
        self.layout.addRow(translate('Tourism individual'), self.individual_scores)

        self.pair_scores = QLineEdit()
        self.pair_scores.setText(
            obj.get_setting('tourism_pair_scores_array', DEFAULT_TOURISM_SCORES)
        )
        self.layout.addRow(translate('Tourism pair'), self.pair_scores)

        self.group_scores = QLineEdit()
        self.group_scores.setText(
            obj.get_setting('tourism_group_scores_array', DEFAULT_TOURISM_SCORES)
        )
        self.layout.addRow(translate('Tourism group'), self.group_scores)

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
        obj.set_setting('tourism_individual_scores_array', self.individual_scores.text())
        obj.set_setting('tourism_pair_scores_array', self.pair_scores.text())
        obj.set_setting('tourism_group_scores_array', self.group_scores.text())
