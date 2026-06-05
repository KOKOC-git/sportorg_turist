from dataclasses import dataclass


@dataclass
class PhotoFinishConfig:
    """
    Настройки подключения фотоствора.

    enabled — включён ли модуль.
    port — последовательный порт: COM3, /dev/tty.usbmodemXXXX и т.п.
    baudrate — скорость COM-порта.
    debounce_ms — защита от повторного срабатывания.
    trigger_text — строка, которую адаптер присылает при пересечении луча.
    """
    enabled: bool = False
    port: str = ""
    baudrate: int = 9600
    debounce_ms: int = 100
    trigger_text: str = "FINISH"
