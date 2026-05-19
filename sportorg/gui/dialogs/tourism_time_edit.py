from PySide6.QtWidgets import QLineEdit

from sportorg.models.tourism import normalize_hms_input


class TourismTimeEdit(QLineEdit):
    """
    Поле для удобного ввода времени штрафа/отсечки.

    Пользователь может вводить:
    30      -> 00:00:30
    130     -> 00:01:30
    1230    -> 00:12:30
    123045  -> 12:30:45
    1:30    -> 00:01:30
    1:02:03 -> 01:02:03
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("HH:MM:SS")
        self.editingFinished.connect(self.normalize)

    def normalize(self):
        text = self.text().strip()
        if not text:
            return
        self.setText(normalize_hms_input(text))
