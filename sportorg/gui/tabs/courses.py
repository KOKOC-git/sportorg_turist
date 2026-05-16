import logging

from PySide6 import QtWidgets
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.dialogs.tourism_stages import TourismStagesDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import CourseMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race
from sportorg.models.tourism import CompetitionType, ensure_tourism_defaults


class CoursesTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.course_table = CoursesTableView(self)
        self.course_layout = QtWidgets.QGridLayout(self)
        self.tourism_widget = None
        self.setup_ui()

    def _is_tourism(self):
        obj = race()
        ensure_tourism_defaults(obj)
        return getattr(obj, 'competition_type', CompetitionType.INDIVIDUAL.value) == CompetitionType.TOURISM.value

    def _clear_layout(self):
        while self.course_layout.count():
            item = self.course_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _open_tourism_stages(self):
        dialog = TourismStagesDialog(GlobalAccess().get_main_window())
        dialog.exec_()
        GlobalAccess().get_main_window().refresh()

    def _setup_tourism_ui(self):
        self._clear_layout()

        panel = QtWidgets.QWidget(self)
        layout = QVBoxLayout(panel)

        label = QLabel(
            'Для вида соревнований «Туризм» вместо обычных дистанций используются этапы.\n'
            'Нажмите кнопку ниже, чтобы добавить, удалить или изменить порядок этапов по группам.'
        )
        label.setWordWrap(True)

        button = QPushButton('Настроить этапы туризма')
        button.clicked.connect(self._open_tourism_stages)

        layout.addWidget(label)
        layout.addWidget(button)
        layout.addStretch(1)

        self.tourism_widget = panel
        self.course_layout.addWidget(panel)

    def _setup_courses_ui(self):
        self._clear_layout()

        self.course_table.setObjectName('CourseTable')
        self.course_table.setModel(CourseMemoryModel())

        def course_double_clicked(index):
            try:
                if index.row() < len(race().courses):
                    dialog = CourseEditDialog(race().courses[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh()
            except Exception as e:
                logging.error(str(e))

        try:
            self.course_table.activated.disconnect()
        except Exception:
            pass

        self.course_table.activated.connect(course_double_clicked)
        self.course_layout.addWidget(self.course_table)

    def setup_ui(self):
        if self._is_tourism():
            self._setup_tourism_ui()
        else:
            self._setup_courses_ui()

    def refresh_view(self):
        self.setup_ui()

    def showEvent(self, event):
        self.setup_ui()
        super().showEvent(event)

    def get_table(self):
        return self.course_table
