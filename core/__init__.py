"""Package core - Logique métier principale"""
from .face_recognition import FaceRecognitionEngine
from .authentication import AuthenticationManager
from .antispoofing import AntiSpoofingDetector

__all__ = [
    'FaceRecognitionEngine',
    'AuthenticationManager',
    'AntiSpoofingDetector'
]