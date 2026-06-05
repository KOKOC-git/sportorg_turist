from datetime import datetime

from sportorg.modules.photo_finish.config import PhotoFinishConfig
from sportorg.modules.photo_finish.device import PhotoFinishDevice
from sportorg.modules.photo_finish.events import PhotoFinishEvent


class PhotoFinishService:
    """
    Сервис фотоствора.

    Отделяет SportOrg от конкретного устройства.
    Снаружи SportOrg получает только событие PhotoFinishEvent.
    """

    def __init__(self, config=None):
        self.config = config or PhotoFinishConfig()
        self.device = None
        self.finish_callback = None
        self.error_callback = None
        self.status_callback = None

    def set_finish_callback(self, callback):
        self.finish_callback = callback

    def set_error_callback(self, callback):
        self.error_callback = callback

    def set_status_callback(self, callback):
        self.status_callback = callback

    def configure(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def start(self):
        if not self.config.enabled:
            self._on_status("Фотоствор выключен в настройках")
            return False

        self.device = PhotoFinishDevice(
            config=self.config,
            on_finish=self._on_finish,
            on_error=self._on_error,
            on_status=self._on_status,
        )
        return self.device.start()

    def stop(self):
        if self.device:
            self.device.stop()
            self.device = None

    def test_finish(self):
        event = PhotoFinishEvent(
            timestamp=datetime.now(),
            raw="TEST",
        )
        self._on_finish(event)

    def _on_finish(self, event):
        if self.finish_callback:
            self.finish_callback(event)

    def _on_error(self, message):
        if self.error_callback:
            self.error_callback(message)
        else:
            print(f"[PHOTO FINISH ERROR] {message}")

    def _on_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            print(f"[PHOTO FINISH] {message}")
