import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time

from sportorg.modules.photo_finish.service import PhotoFinishService


def main():
    parser = argparse.ArgumentParser(description="Проверка модуля фотоствора")
    parser.add_argument("--port", default="", help="COM-порт, например COM3 или /dev/tty.usbmodemXXXX")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--debounce", type=int, default=1000)
    parser.add_argument("--trigger", default="FINISH")
    parser.add_argument("--test", action="store_true", help="Создать тестовый финиш без устройства")
    args = parser.parse_args()

    service = PhotoFinishService()

    def on_finish(event):
        print(f"FINISH: {event.timestamp.isoformat(timespec='milliseconds')} raw={event.raw}")

    def on_error(message):
        print(f"ERROR: {message}")

    def on_status(message):
        print(f"STATUS: {message}")

    service.set_finish_callback(on_finish)
    service.set_error_callback(on_error)
    service.set_status_callback(on_status)

    if args.test:
        service.test_finish()
        return

    service.configure(
        enabled=True,
        port=args.port,
        baudrate=args.baudrate,
        debounce_ms=args.debounce,
        trigger_text=args.trigger,
    )

    if not service.start():
        return

    print("Ожидание сигналов фотоствора. Для выхода нажми Ctrl+C.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка...")
    finally:
        service.stop()


if __name__ == "__main__":
    main()
