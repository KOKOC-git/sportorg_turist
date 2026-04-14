from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from sportorg.language import translate
from sportorg.modules.web_timing.server import WebTimingServer


class WebTimingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('Web timing'))
        self.resize(620, 220)

        self.server = WebTimingServer.instance()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.port = QLineEdit(str(self.server.port))
        self.stage_url = QLabel('')
        self.finish_url = QLabel('')
        self.viewer_summary_url = QLabel('')
        self.viewer_group_url = QLabel('')

        form.addRow(translate('Port'), self.port)
        form.addRow(translate('Stage timing URL'), self.stage_url)
        form.addRow(translate('Finish timing URL'), self.finish_url)
        form.addRow(translate('Viewer summary URL'), self.viewer_summary_url)
        form.addRow(translate('Viewer group URL'), self.viewer_group_url)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton(translate('Start'))
        self.btn_stop = QPushButton(translate('Stop'))
        self.btn_close = QPushButton(translate('Close'))
        self.btn_start.clicked.connect(self.start_server)
        self.btn_stop.clicked.connect(self.stop_server)
        self.btn_close.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)

        self.refresh_urls()

    def refresh_urls(self):
        self.server.ensure_storage()
        self.stage_url.setText(self.server.get_stage_url())
        self.finish_url.setText(self.server.get_finish_url())
        self.viewer_summary_url.setText(self.server.get_viewer_summary_url())
        self.viewer_group_url.setText(self.server.get_viewer_group_url())

    def start_server(self):
        self.server.start(int(self.port.text() or '8088'))
        self.refresh_urls()

    def stop_server(self):
        self.server.stop()
