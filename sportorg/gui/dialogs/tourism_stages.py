from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.tourism import (
    CompetitionType,
    TourismCourse,
    TourismStage,
    ensure_tourism_defaults,
)


class TourismStagesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Tourism stages'))
        self.resize(900, 640)

        ensure_tourism_defaults(race())
        self.current_course_id = None
        self.group_checkboxes = {}

        self.layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.course_label = QLabel('Туристская дистанция')
        self.course_combo = QComboBox()
        self.course_name = QLineEdit()
        self.course_name.setPlaceholderText('Название дистанции')
        self.btn_add_course = QPushButton('Добавить дистанцию')
        self.btn_delete_course = QPushButton('Удалить дистанцию')

        top_row.addWidget(self.course_label)
        top_row.addWidget(self.course_combo, 1)
        top_row.addWidget(self.course_name, 1)
        top_row.addWidget(self.btn_add_course)
        top_row.addWidget(self.btn_delete_course)
        self.layout.addLayout(top_row)

        self.info_label = QLabel(
            'Одна туристская дистанция может быть назначена нескольким группам. '
            'Этапы задаются для дистанции, а группы ниже только привязываются к ней.'
        )
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.groups_area = QScrollArea()
        self.groups_widget = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_widget)
        self.groups_area.setWidget(self.groups_widget)
        self.groups_area.setWidgetResizable(True)
        self.groups_area.setFixedHeight(130)
        self.layout.addWidget(QLabel('Группы, которые используют эту дистанцию:'))
        self.layout.addWidget(self.groups_area)

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

        self.btn_add_course.clicked.connect(self.add_course)
        self.btn_delete_course.clicked.connect(self.delete_course)
        self.btn_add.clicked.connect(self.add_stage)
        self.btn_delete.clicked.connect(self.delete_stage)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)
        self.course_combo.currentIndexChanged.connect(self.change_course)

        self.ensure_initial_courses()
        self.load_courses()
        self.load_data()

    def ensure_initial_courses(self):
        obj = race()
        ensure_tourism_defaults(obj)

        if not getattr(obj, 'tourism_courses', []):
            if obj.courses:
                for course in obj.courses:
                    obj.tourism_courses.append(
                        TourismCourse(name=course.name or f'Дистанция {course.bib}')
                    )
            else:
                obj.tourism_courses.append(TourismCourse(name='Дистанция 1'))

    def load_courses(self):
        self.course_combo.blockSignals(True)
        self.course_combo.clear()

        for course in race().tourism_courses:
            self.course_combo.addItem(course.name, course.id)

        self.course_combo.blockSignals(False)

        if self.course_combo.count() > 0:
            self.current_course_id = self.course_combo.currentData()

    def get_current_course(self):
        course_id = self.course_combo.currentData()
        for course in race().tourism_courses:
            if str(course.id) == str(course_id):
                return course
        return None

    def save_current_course(self):
        course = self.get_current_course()
        if not course:
            return

        name = self.course_name.text().strip()
        if not name:
            raise ValueError('Название дистанции не может быть пустым')

        stages = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            stage_name = name_item.text().strip() if name_item else ''
            if not stage_name:
                raise ValueError('Название этапа не может быть пустым')
            stages.append(
                TourismStage(
                    tourism_course_id=str(course.id),
                    order_num=row + 1,
                    name=stage_name,
                )
            )

        course.name = name
        course.group_ids = [
            group_id
            for group_id, checkbox in self.group_checkboxes.items()
            if checkbox.isChecked()
        ]

        race().tourism_stages = [
            x for x in race().tourism_stages
            if str(getattr(x, 'tourism_course_id', '')) != str(course.id)
        ]
        race().tourism_stages.extend(stages)

    def change_course(self):
        try:
            if self.current_course_id:
                self.save_current_course()
        except Exception:
            # Не мешаем переключению, пользователь сможет сохранить позже.
            pass

        self.current_course_id = self.course_combo.currentData()
        self.load_data()

    def load_groups(self, course):
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.group_checkboxes = {}

        assigned = [str(x) for x in getattr(course, 'group_ids', [])]

        for group in race().groups:
            group_type = (
                group.get_competition_type()
                if hasattr(group, 'get_competition_type')
                else getattr(group, 'competition_type', None)
            ) or getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value)

            if group_type != CompetitionType.TOURISM.value:
                continue

            checkbox = QCheckBox(group.name)
            checkbox.setChecked(str(group.id) in assigned)
            self.group_checkboxes[str(group.id)] = checkbox
            self.groups_layout.addWidget(checkbox)

        self.groups_layout.addStretch(1)

    def load_data(self):
        course = self.get_current_course()
        if not course:
            self.course_name.setText('')
            self.table.setRowCount(0)
            return

        self.course_name.setText(course.name)
        self.load_groups(course)

        stages = [
            x for x in race().tourism_stages
            if str(getattr(x, 'tourism_course_id', '')) == str(course.id)
        ]
        stages = sorted(stages, key=lambda x: x.order_num)

        self.table.setRowCount(len(stages))
        for row, stage in enumerate(stages):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(stage.name))

    def normalize_order_numbers(self):
        for row in range(self.table.rowCount()):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def add_course(self):
        try:
            if self.current_course_id:
                self.save_current_course()
        except Exception as e:
            QMessageBox.warning(self, translate('Error'), str(e))
            return

        number = len(race().tourism_courses) + 1
        course = TourismCourse(name=f'Дистанция {number}')
        race().tourism_courses.append(course)
        self.load_courses()

        index = self.course_combo.findData(course.id)
        if index >= 0:
            self.course_combo.setCurrentIndex(index)

        self.load_data()

    def delete_course(self):
        course = self.get_current_course()
        if not course:
            return

        course_id = str(course.id)
        race().tourism_courses = [
            x for x in race().tourism_courses
            if str(x.id) != course_id
        ]
        race().tourism_stages = [
            x for x in race().tourism_stages
            if str(getattr(x, 'tourism_course_id', '')) != course_id
        ]

        if not race().tourism_courses:
            race().tourism_courses.append(TourismCourse(name='Дистанция 1'))

        self.load_courses()
        self.load_data()

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
        try:
            self.save_current_course()
        except Exception as e:
            QMessageBox.warning(self, translate('Error'), str(e))
            return

        self.accept()
