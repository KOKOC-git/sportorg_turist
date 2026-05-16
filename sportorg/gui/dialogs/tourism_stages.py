from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
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
        self.resize(980, 620)

        ensure_tourism_defaults(race())

        self.current_course_id = None
        self.group_checkboxes = {}

        root = QVBoxLayout(self)

        info = QLabel(
            'Дистанции туризма: одна дистанция может быть назначена нескольким группам. '
            'Этапы создаются внутри выбранной дистанции.'
        )
        info.setWordWrap(True)
        root.addWidget(info)

        main = QHBoxLayout()
        root.addLayout(main)

        # Левая часть — список дистанций
        left = QVBoxLayout()
        main.addLayout(left, 1)

        left.addWidget(QLabel('Дистанции'))

        self.course_list = QListWidget()
        self.course_list.setSelectionMode(QAbstractItemView.SingleSelection)
        left.addWidget(self.course_list, 1)

        course_buttons = QHBoxLayout()
        self.btn_add_course = QPushButton('Добавить')
        self.btn_rename_course = QPushButton('Переименовать')
        self.btn_delete_course = QPushButton('Удалить')
        course_buttons.addWidget(self.btn_add_course)
        course_buttons.addWidget(self.btn_rename_course)
        course_buttons.addWidget(self.btn_delete_course)
        left.addLayout(course_buttons)

        # Правая часть — этапы и группы
        right = QVBoxLayout()
        main.addLayout(right, 2)

        right.addWidget(QLabel('Этапы выбранной дистанции'))

        self.stage_table = QTableWidget(self)
        self.stage_table.setColumnCount(2)
        self.stage_table.setHorizontalHeaderLabels(['Порядок', 'Название этапа'])
        right.addWidget(self.stage_table, 2)

        stage_buttons = QHBoxLayout()
        self.btn_add_stage = QPushButton('Добавить этап')
        self.btn_delete_stage = QPushButton('Удалить этап')
        self.btn_up = QPushButton('Вверх')
        self.btn_down = QPushButton('Вниз')
        stage_buttons.addWidget(self.btn_add_stage)
        stage_buttons.addWidget(self.btn_delete_stage)
        stage_buttons.addWidget(self.btn_up)
        stage_buttons.addWidget(self.btn_down)
        right.addLayout(stage_buttons)

        right.addWidget(QLabel('Группы, которые используют выбранную дистанцию'))

        self.groups_widget = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_widget)
        right.addWidget(self.groups_widget, 1)

        bottom = QHBoxLayout()
        self.btn_save = QPushButton(translate('Save'))
        self.btn_cancel = QPushButton(translate('Cancel'))
        bottom.addStretch(1)
        bottom.addWidget(self.btn_save)
        bottom.addWidget(self.btn_cancel)
        root.addLayout(bottom)

        self.course_list.currentItemChanged.connect(self.on_course_changed)
        self.btn_add_course.clicked.connect(self.add_course)
        self.btn_rename_course.clicked.connect(self.rename_course)
        self.btn_delete_course.clicked.connect(self.delete_course)

        self.btn_add_stage.clicked.connect(self.add_stage)
        self.btn_delete_stage.clicked.connect(self.delete_stage)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

        self.load_courses()

    def load_courses(self):
        ensure_tourism_defaults(race())

        self.course_list.clear()

        for course in race().tourism_courses:
            item = QListWidgetItem(course.name or 'Без названия')
            item.setData(Qt.UserRole, course.id)
            self.course_list.addItem(item)

        if self.course_list.count() > 0:
            self.course_list.setCurrentRow(0)
        else:
            self.clear_right_panel()

    def clear_right_panel(self):
        self.current_course_id = None
        self.stage_table.setRowCount(0)
        self.reload_group_checkboxes(None)

    def get_current_course(self):
        item = self.course_list.currentItem()
        if item is None:
            return None

        course_id = item.data(Qt.UserRole)
        for course in race().tourism_courses:
            if course.id == course_id:
                return course

        return None

    def on_course_changed(self):
        self.load_selected_course()

    def load_selected_course(self):
        course = self.get_current_course()
        if not course:
            self.clear_right_panel()
            return

        self.current_course_id = course.id

        stages = [
            x for x in race().tourism_stages
            if str(getattr(x, 'tourism_course_id', '')) == str(course.id)
        ]
        stages = sorted(stages, key=lambda x: x.order_num)

        self.stage_table.setRowCount(len(stages))
        for row, stage in enumerate(stages):
            self.stage_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.stage_table.setItem(row, 1, QTableWidgetItem(stage.name))

        self.reload_group_checkboxes(course)

    def reload_group_checkboxes(self, course):
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        self.group_checkboxes = {}

        for group in race().groups:
            group_type_getter = getattr(group, 'get_competition_type', None)
            group_type = (
                group.get_competition_type()
                if callable(group_type_getter)
                else getattr(group, 'competition_type', None)
            ) or getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value)

            if group_type != CompetitionType.TOURISM.value:
                continue

            group_id = str(group.id)
            checkbox = QCheckBox(group.name)
            checkbox.setChecked(course is not None and group_id in [str(x) for x in course.group_ids])
            self.group_checkboxes[group_id] = checkbox
            self.groups_layout.addWidget(checkbox)

        self.groups_layout.addStretch(1)

    def add_course(self):
        name, ok = QInputDialog.getText(self, 'Новая дистанция', 'Название дистанции:')
        if not ok:
            return

        name = name.strip()
        if not name:
            QMessageBox.warning(self, translate('Error'), 'Название дистанции не может быть пустым')
            return

        course = TourismCourse(name=name)
        race().tourism_courses.append(course)
        self.load_courses()

        for row in range(self.course_list.count()):
            item = self.course_list.item(row)
            if item.data(Qt.UserRole) == course.id:
                self.course_list.setCurrentRow(row)
                break

    def rename_course(self):
        course = self.get_current_course()
        if not course:
            return

        name, ok = QInputDialog.getText(self, 'Переименовать дистанцию', 'Название дистанции:', text=course.name)
        if not ok:
            return

        name = name.strip()
        if not name:
            QMessageBox.warning(self, translate('Error'), 'Название дистанции не может быть пустым')
            return

        course.name = name
        self.load_courses()

    def delete_course(self):
        course = self.get_current_course()
        if not course:
            return

        answer = QMessageBox.question(
            self,
            'Удалить дистанцию',
            f'Удалить дистанцию «{course.name}» и все её этапы?',
        )

        if answer != QMessageBox.Yes:
            return

        race().tourism_stages = [
            x for x in race().tourism_stages
            if str(getattr(x, 'tourism_course_id', '')) != str(course.id)
        ]
        race().tourism_courses = [
            x for x in race().tourism_courses
            if str(x.id) != str(course.id)
        ]
        self.load_courses()

    def normalize_order_numbers(self):
        for row in range(self.stage_table.rowCount()):
            self.stage_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def add_stage(self):
        if not self.get_current_course():
            QMessageBox.warning(self, translate('Error'), 'Сначала создайте дистанцию')
            return

        row = self.stage_table.rowCount()
        self.stage_table.insertRow(row)
        self.stage_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.stage_table.setItem(row, 1, QTableWidgetItem(''))

    def delete_stage(self):
        row = self.stage_table.currentRow()
        if row < 0:
            return

        self.stage_table.removeRow(row)
        self.normalize_order_numbers()

    def move_up(self):
        row = self.stage_table.currentRow()
        if row <= 0:
            return

        for col in range(self.stage_table.columnCount()):
            upper = self.stage_table.takeItem(row - 1, col)
            current = self.stage_table.takeItem(row, col)
            self.stage_table.setItem(row - 1, col, current)
            self.stage_table.setItem(row, col, upper)

        self.stage_table.setCurrentCell(row - 1, 0)
        self.normalize_order_numbers()

    def move_down(self):
        row = self.stage_table.currentRow()
        if row < 0 or row >= self.stage_table.rowCount() - 1:
            return

        for col in range(self.stage_table.columnCount()):
            current = self.stage_table.takeItem(row, col)
            lower = self.stage_table.takeItem(row + 1, col)
            self.stage_table.setItem(row, col, lower)
            self.stage_table.setItem(row + 1, col, current)

        self.stage_table.setCurrentCell(row + 1, 0)
        self.normalize_order_numbers()

    def save_current_course(self):
        course = self.get_current_course()
        if not course:
            return

        stages = []
        for row in range(self.stage_table.rowCount()):
            name_item = self.stage_table.item(row, 1)
            name = name_item.text().strip() if name_item else ''

            if not name:
                raise ValueError('Название этапа не может быть пустым')

            stages.append(
                TourismStage(
                    tourism_course_id=course.id,
                    order_num=row + 1,
                    name=name,
                )
            )

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

    def save(self):
        try:
            self.save_current_course()
        except Exception as e:
            QMessageBox.warning(self, translate('Error'), str(e))
            return

        self.accept()
