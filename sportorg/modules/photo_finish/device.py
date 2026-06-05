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

    Поддерживает два режима:
    1. trigger_text = "FINISH" — ждёт текстовую строку FINISH.
    2. trigger_text = "*" — любое поступление байтов в COM-порт считается финишем.

    Для MOXA UPort 1110 + ФФ054 сейчас нужен режим "*",
    потому что при срабатывании фотоствор присылает байты 00 00.
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
                timeout=0.01,
            )

            # Для RS-232 адаптеров иногда полезно явно поднять линии.
            try:
                self._serial.dtr = True
                self._serial.rts = True
            except Exception:
                pass

            try:
                self._serial.reset_input_buffer()
            except Exception:
                pass

        except Exception as exc:
            self._emit_error(f"Не удалось открыть порт фотоствора: {exc}")
            self._running = False
            return

        while self._running:
            try:
                raw = self._serial.read(1)

                if raw:
                    try:
                        waiting = self._serial.in_waiting
                    except Exception:
                        waiting = 0
                    if waiting:
                        raw += self._serial.read(waiting)

                if not raw:
                    continue

                trigger_text = str(getattr(self.config, "trigger_text", "FINISH")).strip()

                raw_hex = raw.hex(" ")
                raw_text = raw.decode("utf-8", errors="ignore").strip()

                # Режим для ФФ054 через MOXA:
                # любые пришедшие байты считаем финишем.
                if trigger_text == "*":
                    self._handle_trigger(raw=raw_text if raw_text else raw_hex)
                    continue

                # Старый режим: ждём конкретный текст, например FINISH.
                if not raw_text:
                    continue

                if raw_text == trigger_text:
                    self._handle_trigger(raw=raw_text)

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