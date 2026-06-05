import threading
import time
from datetime import datetime

try:
    import serial
except ImportError:
    serial = None

from sportorg.modules.photo_finish.events import PhotoFinishEvent


class PhotoFinishDevice:
    """
    Низкоуровневое устройство фотоствора.

    Ожидает строку trigger_text в COM-порту.
    Например, Arduino/USB-COM адаптер отправляет:
        FINISH
    """

    def __init__(self, config, on_finish=None, on_error=None, on_status=None):
        self.config = config
        self.on_finish = on_finish
        self.on_error = on_error
        self.on_status = on_status

        self._thread = None
        self._running = False
        self._serial = None
        self._last_trigger_time_ms = 0

    def start(self):
        if serial is None:
            self._emit_error(
                "Не установлен pyserial. Установите зависимость: pip install pyserial"
            )
            return False

        if not self.config.port:
            self._emit_error("Не выбран порт фотоствора")
            return False

        if self._running:
            return True

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._emit_status("Фотоствор запущен")
        return True

    def stop(self):
        self._running = False

        try:
            if self._serial:
                self._serial.close()
        except Exception:
            pass

        self._serial = None
        self._emit_status("Фотоствор остановлен")

    def is_running(self):
        return self._running

    def _run(self):
        try:
            self._serial = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=0.2,
            )
        except Exception as exc:
            self._emit_error(f"Не удалось открыть порт фотоствора: {exc}")
            self._running = False
            return

        while self._running:
            try:
                raw = self._serial.readline()

                if not raw:
                    continue

                text = raw.decode("utf-8", errors="ignore").strip()

                if not text:
                    continue

                if text == self.config.trigger_text:
                    self._handle_trigger(raw=text)

            except Exception as exc:
                self._emit_error(f"Ошибка чтения фотоствора: {exc}")
                time.sleep(0.5)

    def _handle_trigger(self, raw=""):
        now_ms = time.monotonic() * 1000

        if now_ms - self._last_trigger_time_ms < self.config.debounce_ms:
            return

        self._last_trigger_time_ms = now_ms

        event = PhotoFinishEvent(
            timestamp=datetime.now(),
            raw=raw,
        )

        if self.on_finish:
            self.on_finish(event)

    def _emit_error(self, message):
        if self.on_error:
            self.on_error(message)

    def _emit_status(self, message):
        if self.on_status:
            self.on_status(message)
