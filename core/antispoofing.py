"""Détection anti-spoofing pour prévenir les attaques par photos/vidéos"""
import cv2
import numpy as np
from typing import Tuple, Optional
from utils.logger import Logger
from config.settings import (
    ANTISPOOFING_THRESHOLD,
    BLINK_DETECTION_ENABLED,
    HEAD_TURN_DETECTION_ENABLED
)

logger = Logger()


class AntiSpoofingDetector:
    """Classe pour détecter les tentatives de spoofing"""

    def __init__(self):
        self.ear_threshold = 0.25  # Eye Aspect Ratio pour détection de clignement
        self.head_turn_threshold = 15  # Degrés pour détection de mouvement de tête
        self.blink_counter = 0
        self.head_turn_counter = 0
        logger.log_info("Détecteur anti-spoofing initialisé")

    def detect_blink(self, frame: np.ndarray, face_location: Tuple) -> bool:
        """
        Détecter un clignement d'œil

        Args:
            frame: Image
            face_location: (top, right, bottom, left)

        Returns:
            True si un clignement est détecté
        """
        if not BLINK_DETECTION_ENABLED:
            return True

        try:
            # Cette fonction nécessiterait dlib ou mediapipe pour détecter les landmarks
            # Implémentation simplifiée pour la démo
            # TODO: Implémenter avec dlib facial landmarks pour production

            # Pour l'instant, simulation basée sur des variations d'intensité
            top, right, bottom, left = face_location
            eye_region = frame[top:bottom, left:right]

            # Convertir en niveaux de gris
            gray = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)

            # Détecter des variations (simplification)
            mean_intensity = np.mean(gray)

            # Logique simplifiée (à remplacer par une vraie détection)
            blink_detected = np.random.random() > 0.7

            if blink_detected:
                self.blink_counter += 1
                logger.log_debug("Clignement détecté")

            return blink_detected

        except Exception as e:
            logger.log_error(f"Erreur détection blink: {e}")
            return False

    def detect_head_turn(self, frame: np.ndarray, face_location: Tuple) -> bool:
        """
        Détecter un mouvement de tête

        Args:
            frame: Image
            face_location: (top, right, bottom, left)

        Returns:
            True si un mouvement est détecté
        """
        if not HEAD_TURN_DETECTION_ENABLED:
            return True

        try:
            # TODO: Implémenter avec pose estimation (dlib, mediapipe)
            # Implémentation simplifiée pour la démo

            top, right, bottom, left = face_location
            face_width = right - left
            face_height = bottom - top

            # Vérifier le ratio largeur/hauteur pour détecter une rotation
            ratio = face_width / face_height if face_height > 0 else 0

            # Logique simplifiée
            head_turn_detected = np.random.random() > 0.6

            if head_turn_detected:
                self.head_turn_counter += 1
                logger.log_debug("Mouvement de tête détecté")

            return head_turn_detected

        except Exception as e:
            logger.log_error(f"Erreur détection head turn: {e}")
            return False

    def detect_texture_analysis(self, frame: np.ndarray, face_location: Tuple) -> float:
        """
        Analyser la texture pour détecter une photo/écran

        Args:
            frame: Image
            face_location: Coordonnées du visage

        Returns:
            Score de texture (0-1)
        """
        try:
            top, right, bottom, left = face_location
            face_region = frame[top:bottom, left:right]

            # Convertir en niveaux de gris
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)

            # Calculer le Laplacien (mesure de netteté)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()

            # Normaliser le score (valeurs typiques: 100-500 pour visages réels)
            texture_score = min(variance / 500.0, 1.0)

            logger.log_debug(f"Score de texture: {texture_score:.2f}")
            return texture_score

        except Exception as e:
            logger.log_error(f"Erreur analyse texture: {e}")
            return 0.5

    def calculate_liveness_score(self, blink_detected: bool,
                                 head_turn_detected: bool,
                                 texture_score: float = 0.5) -> float:
        """
        Calculer un score de vivacité global

        Args:
            blink_detected: Clignement détecté
            head_turn_detected: Mouvement de tête détecté
            texture_score: Score d'analyse de texture

        Returns:
            Score entre 0 et 1 (1 = personne vivante)
        """
        score = 0.0

        # Clignement: 30%
        if BLINK_DETECTION_ENABLED and blink_detected:
            score += 0.3
        elif not BLINK_DETECTION_ENABLED:
            score += 0.3

        # Mouvement de tête: 40%
        if HEAD_TURN_DETECTION_ENABLED and head_turn_detected:
            score += 0.4
        elif not HEAD_TURN_DETECTION_ENABLED:
            score += 0.4

        # Texture: 30%
        score += texture_score * 0.3

        logger.log_info(f"Score de vivacité: {score:.2f}")
        return score

    def is_live(self, liveness_score: float) -> bool:
        """
        Vérifier si le score indique une personne réelle

        Args:
            liveness_score: Score de vivacité

        Returns:
            True si la personne est jugée réelle
        """
        is_live = liveness_score >= ANTISPOOFING_THRESHOLD

        if is_live:
            logger.log_info("Personne réelle détectée")
        else:
            logger.log_warning(f"Tentative de spoofing suspectée (score: {liveness_score:.2f})")

        return is_live

    def reset_counters(self):
        """Réinitialiser les compteurs"""
        self.blink_counter = 0
        self.head_turn_counter = 0

    def get_detection_stats(self) -> dict:
        """Obtenir les statistiques de détection"""
        return {
            'blink_count': self.blink_counter,
            'head_turn_count': self.head_turn_counter
        }