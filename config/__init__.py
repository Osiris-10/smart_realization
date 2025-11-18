"""Package de configuration"""
from .database import DB_CONFIG
from .settings import *

__all__ = [
    'DB_CONFIG',
    'FACE_RECOGNITION_TOLERANCE',
    'MAX_FAILED_FACE_ATTEMPTS',
    'MAX_FAILED_PIN_ATTEMPTS',
    'CAMERA_INDEX',
    'WINDOW_SIZE'
]