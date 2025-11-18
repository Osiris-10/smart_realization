"""Modèles de données pour les tables de la base de données"""
from datetime import datetime
from typing import Optional, Dict, Any


class Personne:
    """Modèle pour la table personne"""

    def __init__(self, personne_id: int = None, username: str = None,
                 password: str = None, email: str = None,
                 role: str = 'USER', created_at: datetime = None,
                 is_active: bool = True):
        self.personne_id = personne_id
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.created_at = created_at or datetime.now()
        self.is_active = is_active

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            'personne_id': self.personne_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'is_active': self.is_active
        }

    @staticmethod
    def from_db_row(row: tuple) -> 'Personne':
        """Créer une instance depuis une ligne de la BD"""
        if not row:
            return None
        return Personne(
            personne_id=row[0],
            username=row[1],
            password=row[2],
            email=row[3],
            role=row[4],
            created_at=row[5],
            is_active=bool(row[6])
        )

    def __repr__(self):
        return f"<Personne(id={self.personne_id}, username='{self.username}')>"


class FaceProfile:
    """Modèle pour la table face_profiles"""

    def __init__(self, profile_id: int = None, personne_id: int = None,
                 embedding: str = None, image_url: str = None):
        self.profile_id = profile_id
        self.personne_id = personne_id
        self.embedding = embedding
        self.image_url = image_url

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            'profile_id': self.profile_id,
            'personne_id': self.personne_id,
            'embedding': self.embedding,
            'image_url': self.image_url
        }

    @staticmethod
    def from_db_row(row: tuple) -> 'FaceProfile':
        """Créer une instance depuis une ligne de la BD"""
        if not row:
            return None
        return FaceProfile(
            profile_id=row[0],
            personne_id=row[1],
            embedding=row[2],
            image_url=row[3]
        )

    def __repr__(self):
        return f"<FaceProfile(id={self.profile_id}, personne_id={self.personne_id})>"


class AccesLog:
    """Modèle pour la table acces_log"""

    def __init__(self, access_id: int = None, personne_id: int = None,
                 access_result: str = None, access_method: str = None,
                 image_url: str = None, horaire: datetime = None,
                 similarity_score: float = None):
        self.access_id = access_id
        self.personne_id = personne_id
        self.access_result = access_result  # GRANTED, DENIED
        self.access_method = access_method  # FACE_PIN, PIN_ONLY, FACE_ONLY
        self.image_url = image_url
        self.horaire = horaire or datetime.now()
        self.similarity_score = similarity_score

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            'access_id': self.access_id,
            'personne_id': self.personne_id,
            'access_result': self.access_result,
            'access_method': self.access_method,
            'image_url': self.image_url,
            'horaire': self.horaire,
            'similarity_score': self.similarity_score
        }

    @staticmethod
    def from_db_row(row: tuple) -> 'AccesLog':
        """Créer une instance depuis une ligne de la BD"""
        if not row:
            return None
        return AccesLog(
            access_id=row[0],
            personne_id=row[1],
            access_result=row[2],
            access_method=row[3],
            image_url=row[4],
            horaire=row[5],
            similarity_score=row[6]
        )

    def __repr__(self):
        return f"<AccesLog(id={self.access_id}, result='{self.access_result}')>"


class AttemptsCounter:
    """Modèle pour la table attempts_counter"""

    def __init__(self, counter_id: int = None, personne_id: int = None,
                 failed_face_attempts: int = 0, failed_pin_attempts: int = 0):
        self.counter_id = counter_id
        self.personne_id = personne_id
        self.failed_face_attempts = failed_face_attempts
        self.failed_pin_attempts = failed_pin_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            'counter_id': self.counter_id,
            'personne_id': self.personne_id,
            'failed_face_attempts': self.failed_face_attempts,
            'failed_pin_attempts': self.failed_pin_attempts
        }

    @staticmethod
    def from_db_row(row: tuple) -> 'AttemptsCounter':
        """Créer une instance depuis une ligne de la BD"""
        if not row:
            return None
        return AttemptsCounter(
            counter_id=row[0],
            personne_id=row[1],
            failed_face_attempts=row[2],
            failed_pin_attempts=row[3]
        )

    def __repr__(self):
        return f"<AttemptsCounter(id={self.counter_id}, face={self.failed_face_attempts}, pin={self.failed_pin_attempts})>"


class AntiSpoofing:
    """Modèle pour la table antispoofing"""

    def __init__(self, antispoof_id: int = None, personne_id: int = None,
                 blink_detected: bool = False, headturn_detected: bool = False,
                 antispoof_score: float = 0.0, jour: datetime.date = None,
                 horaire: datetime = None):
        self.antispoof_id = antispoof_id
        self.personne_id = personne_id
        self.blink_detected = blink_detected
        self.headturn_detected = headturn_detected
        self.antispoof_score = antispoof_score
        self.jour = jour or datetime.now().date()
        self.horaire = horaire or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            'antispoof_id': self.antispoof_id,
            'personne_id': self.personne_id,
            'blink_detected': self.blink_detected,
            'headturn_detected': self.headturn_detected,
            'antispoof_score': self.antispoof_score,
            'jour': self.jour,
            'horaire': self.horaire
        }

    @staticmethod
    def from_db_row(row: tuple) -> 'AntiSpoofing':
        """Créer une instance depuis une ligne de la BD"""
        if not row:
            return None
        return AntiSpoofing(
            antispoof_id=row[0],
            personne_id=row[1],
            blink_detected=bool(row[2]),
            headturn_detected=bool(row[3]),
            antispoof_score=row[4],
            jour=row[5],
            horaire=row[6]
        )

    def __repr__(self):
        return f"<AntiSpoofing(id={self.antispoof_id}, score={self.antispoof_score})>"