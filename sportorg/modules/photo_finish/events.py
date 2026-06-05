from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PhotoFinishEvent:
    """
    Событие фотоствора.

    timestamp — локальное время компьютера в момент принятия импульса.
    source — источник события.
    raw — исходная строка/сигнал от устройства.
    """
    timestamp: datetime
    source: str = "photo_finish"
    raw: str = ""
