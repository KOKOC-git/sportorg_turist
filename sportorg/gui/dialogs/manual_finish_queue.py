from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork.teamwork import Teamwork
from sportorg.services.manual_finish_queue import (
    add_pending_finish,
    assign_bib_to_finish,
    assign_bib_to_oldest,
    get_pending_items,
    remove_last_pending,
    remove_pending_by_id,
)


class ManualFinishQueueDialog(QDialog):
    def __init__(self, app=None, parent=None):
        parent = parent or GlobalAccess().get_main_window()
        super().__init__(parent)
        self.app = app
        self.setWindowTitle(translate('Manual finish queue'))
        self.resize(760, 360)
        self.setModal(False)

        self.layout = QVBoxLayout(self)

        self.label = QLabel(translate('Finish arrival order'))
        self.layout.addWidget(self.label)

        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                translate('Arrival order'),
                translate('Finish time'),
                translate('Source'),
                translate('Raw signal'),
                translate('Bib'),
                translate('Status'),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        input_row = QHBoxLayout()
        self.input_label = QLabel(translate('Bib'))
        self.input_bib = QLineEdit()
        self.input_bib.returnPressed.connect(self.assign_current)
        self.btn_assign = QPushButton(translate('Assign or correct'))
        self.btn_assign.clicked.connect(self.assign_current)
        input_row.addWidget(self.input_label)
        input_row.addWidget(self.input_bib)
        input_row.addWidget(self.btn_assign)
        self.layout.addLayout(input_row)

        btn_row = QHBoxLayout()
        self.btn_remove_last = QPushButton(translate('Remove last'))
        self.btn_remove_selected = QPushButton(translate('Remove selected'))
        self.btn_close = QPushButton(translate('Close'))
        self.btn_remove_last.clicked.connect(self.remove_last)
        self.btn_remove_selected.clicked.connect(self.remove_selected)
        self.btn_close.clicked.connect(self.close)
        btn_row.addWidget(self.btn_remove_last)
        btn_row.addWidget(self.btn_remove_selected)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_close)
        self.layout.addLayout(btn_row)

        self.shortcut_add_finish = QShortcut(QKeySequence('F3'), self)
        self.shortcut_add_finish.activated.connect(self.add_finish_by_shortcut)

        self.refresh_data()
        self.keep_focus()

    def focus_input(self):
        self.input_bib.setFocus()
        self.input_bib.selectAll()

    def refresh_data(self):
        items = get_pending_items(race())
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            finish_time = item.get('finish_time_msec', 0)
            time_text = ''
            if finish_time:
                from sportorg.common.otime import OTime

                time_text = OTime(msec=int(finish_time)).to_str()

            status = str(item.get('status', 'pending'))
            status_text = (
                translate('Assigned')
                if status == 'assigned'
                else translate('Waiting for bib')
            )

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(item.get('arrival_order', row + 1))),
            )
            self.table.setItem(row, 1, QTableWidgetItem(time_text))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('source', 'manual'))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('raw', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('bib', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(status_text))
            self.table.item(row, 0).setData(Qt.UserRole, item.get('id'))

        pending_row = next(
            (
                row
                for row, item in enumerate(items)
                if item.get('status', 'pending') == 'pending'
            ),
            -1,
        )
        if pending_row >= 0:
            self.table.selectRow(pending_row)
        else:
            self.table.clearSelection()

    def keep_focus(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.focus_input()

    def add_finish_by_shortcut(self):
        add_pending_finish(race())
        self.refresh_data()
        self.keep_focus()

    def assign_current(self):
        bib = self.input_bib.text().strip()
        if not bib:
            return
        try:
            selected_row = self.table.currentRow()
            selected_item = (
                self.table.item(selected_row, 0)
                if selected_row >= 0
                else None
            )
            item_id = selected_item.data(Qt.UserRole) if selected_item else None
            result = (
                assign_bib_to_finish(race(), item_id, int(bib))
                if item_id
                else assign_bib_to_oldest(race(), int(bib))
            )
            Teamwork().send(result.to_dict())
            live_client.send(result)
            ResultCalculation(race()).process_results()
            if self.app:
                self.app.refresh()
            elif GlobalAccess().get_main_window():
                GlobalAccess().get_main_window().refresh()
            self.input_bib.clear()
            self.refresh_data()
            self.keep_focus()
        except Exception as e:
            QMessageBox.warning(self, translate('Error'), str(e))

    def remove_last(self):
        remove_last_pending(race())
        self.refresh_data()
        self.keep_focus()

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if not item:
            return
        item_id = item.data(Qt.UserRole)
        remove_pending_by_id(race(), item_id)
        self.refresh_data()
        self.keep_focus()
