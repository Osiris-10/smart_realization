"""Anti-spoofing RAPIDE - Détection gauche/droite simple"""
import cv2
import numpy as np
from typing import Tuple, Optional
import time
from utils.logger import Logger
from config.settings import (
    ANTISPOOFING_THRESHOLD,
    BLINK_DETECTION_ENABLED,
    HEAD_TURN_DETECTION_ENABLED
)

logger = Logger()


class AntiSpoofingDetector:
    """Détecteur RAPIDE - Mouvement gauche/droite simple et tolérant"""

    def __init__(self):
        # États des mouvements
        self.movement_detected_left = False
        self.movement_detected_right = False

        # Position de référence (centre initial du visage)
        self.reference_x = None
        self.reference_width = None
        
        # Historique des positions pour stabilité
        self.position_history = []
        self.history_size = 3  # Moyenne sur 3 frames

        # Seuils TRÈS FACILES
        self.movement_threshold = 0.12  # 12% de déplacement suffit (très facile)

        # Compteur
        self.head_turn_counter = 0
        
        # Temps de validation
        self.validation_time = None

        logger.log_info("✅ Anti-spoofing RAPIDE initialisé")

    def detect_blink(self, frame: np.ndarray, face_location: Tuple) -> bool:
        """Désactivé - on utilise uniquement le mouvement de tête"""
        return True

    def detect_head_turn(self, frame: np.ndarray, face_location: Tuple) -> bool:
        """
        Détection RAPIDE et TOLÉRANTE du mouvement gauche/droite
        - Très permissif sur la distance
        - Accepte les mouvements rapides
        - Ne perd pas le tracking facilement
        """
        if not HEAD_TURN_DETECTION_ENABLED:
            return True

        try:
            top, right, bottom, left = face_location

            # Centre et largeur du visage
            center_x = (left + right) // 2
            face_width = right - left

            # Ajouter à l'historique pour stabilité
            self.position_history.append(center_x)
            if len(self.position_history) > self.history_size:
                self.position_history.pop(0)
            
            # Utiliser la moyenne pour plus de stabilité
            smooth_x = sum(self.position_history) / len(self.position_history)

            # Première frame : définir référence
            if self.reference_x is None:
                self.reference_x = smooth_x
                self.reference_width = face_width
                logger.log_info(f"📍 Position initiale: {int(smooth_x)}px")
                return False

            # Calculer le déplacement relatif (par rapport à la largeur du visage)
            displacement = smooth_x - self.reference_x
            ratio = displacement / self.reference_width

            # === DÉTECTION GAUCHE ===
            # Le visage s'est déplacé vers la GAUCHE de l'écran (ratio négatif)
            if ratio < -self.movement_threshold:
                if not self.movement_detected_left:
                    self.movement_detected_left = True
                    logger.log_info(f"✅ GAUCHE détecté ({ratio*100:.0f}%)")

            # === DÉTECTION DROITE ===
            # Le visage s'est déplacé vers la DROITE de l'écran (ratio positif)
            if ratio > self.movement_threshold:
                if not self.movement_detected_right:
                    self.movement_detected_right = True
                    logger.log_info(f"✅ DROITE détecté ({ratio*100:.0f}%)")

            # === VALIDATION ===
            # Si les deux mouvements ont été détectés = personne réelle
            if self.movement_detected_left and self.movement_detected_right:
                self.head_turn_counter += 1
                logger.log_info(f"🎉 ANTI-SPOOFING VALIDÉ ! (gauche + droite)")
                return True

            return False

        except Exception as e:
            logger.log_error(f"Erreur détection: {e}")
            return False

    def detect_texture_analysis(self, frame: np.ndarray, face_location: Tuple) -> float:
        """Texture minimale"""
        try:
            top, right, bottom, left = face_location
            h = bottom - top
            w = right - left
            roi = frame[top + h//3:bottom - h//3, left + w//3:right - w//3]

            if roi.size == 0:
                return 0.8

            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            var = lap.var()
            score = min(var / 150.0, 1.0)
            return max(score, 0.6)

        except:
            return 0.8

    def calculate_liveness_score(self, blink_detected: bool,
                                 head_turn_detected: bool,
                                 texture_score: float = 0.8) -> float:
        """Score simplifié"""
        score = 0.0
        if HEAD_TURN_DETECTION_ENABLED and head_turn_detected:
            score += 0.8
        elif not HEAD_TURN_DETECTION_ENABLED:
            score += 0.8
        score += texture_score * 0.2
        return score

    def is_live(self, liveness_score: float) -> bool:
        """Vérification"""
        is_live = liveness_score >= ANTISPOOFING_THRESHOLD
        if is_live:
            logger.log_info(f"✅ Réel ({liveness_score:.2f})")
        else:
            logger.log_warning(f"❌ Suspect ({liveness_score:.2f})")
        return is_live

    def reset_counters(self):
        """Réinitialiser tous les compteurs et états"""
        self.head_turn_counter = 0
        self.movement_detected_left = False
        self.movement_detected_right = False
        self.reference_x = None
        self.reference_width = None
        self.position_history = []
        self.validation_time = None
        logger.log_info("🔄 Anti-spoofing réinitialisé")

    def get_detection_stats(self) -> dict:
        """Retourner les statistiques de détection"""
        return {
            'blink_count': 0,
            'head_turn_count': self.head_turn_counter,
            'left_movement': self.movement_detected_left,
            'right_movement': self.movement_detected_right,
            'center_confirmed': True,
            'threshold': self.movement_threshold
        }
    
    def get_progress(self) -> str:
        """Retourner le progrès sous forme de texte"""
        if self.movement_detected_left and self.movement_detected_right:
            return "✅ Validé"
        elif self.movement_detected_left:
            return "↩️ Gauche OK - Tournez à DROITE"
        elif self.movement_detected_right:
            return "↪️ Droite OK - Tournez à GAUCHE"
        else:
            return "Tournez la tête GAUCHE puis DROITE"