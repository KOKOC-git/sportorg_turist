import logging

from PySide6 import QtWidgets
from PySide6.QtWidgets import QPushButton, QVBoxLayout

from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.dialogs.tourism_stages import TourismStagesDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import CourseMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race
from sportorg.models.tourism import CompetitionType, ensure_tourism_defaults, repair_tourism_courses_from_stages


class CoursesTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.course_table = CoursesTableView(self)
        self.course_layout = QtWidgets.QGridLayout(self)
        self.tourism_button = None
        self.setup_ui()

    def _is_tourism(self):
        obj = race()
        ensure_tourism_defaults(obj)
        repair_tourism_courses_from_stages(obj)
        repair_tourism_courses_from_stages(obj)
        return getattr(obj, 'competition_type', CompetitionType.INDIVIDUAL.value) == CompetitionType.TOURISM.value

    def _open_tourism_stages(self):
        dialog = TourismStagesDialog(GlobalAccess().get_main_window())
        dialog.exec_()
        GlobalAccess().get_main_window().refresh()

    def setup_ui(self):
        wrapper = QtWidgets.QWidget(self)
        wrapper_layout = QVBoxLayout(wrapper)

        self.tourism_button = QPushButton('Настроить этапы туризма')
        self.tourism_button.clicked.connect(self._open_tourism_stages)
        wrapper_layout.addWidget(self.tourism_button)

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

        self.course_table.activated.connect(course_double_clicked)
        wrapper_layout.addWidget(self.course_table)

        self.course_layout.addWidget(wrapper)

        self.refresh_view()

    def refresh_view(self):
        if self.tourism_button:
            self.tourism_button.setVisible(self._is_tourism())

    def showEvent(self, event):
        self.refresh_view()
        super().showEvent(event)

    def get_table(self):
        return self.course_table
