from sportorg.modules.photo_finish.config import PhotoFinishConfig
from sportorg.modules.photo_finish.events import PhotoFinishEvent
from sportorg.modules.photo_finish.service import PhotoFinishService

photo_finish_service = PhotoFinishService()

__all__ = [
    "PhotoFinishConfig",
    "PhotoFinishEvent",
    "PhotoFinishService",
    "photo_finish_service",
]
