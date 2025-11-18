"""Moteur de reconnaissance faciale"""
import face_recognition
import numpy as np
from typing import List, Tuple, Optional
from config.settings import FACE_RECOGNITION_TOLERANCE, FACE_DETECTION_MODEL, SIMILARITY_THRESHOLD
from utils.logger import Logger
from utils.encryption import EncryptionManager

logger = Logger()


class FaceRecognitionEngine:
    """Classe pour gérer la reconnaissance faciale"""

    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.known_passwords = []
        logger.log_info("Moteur de reconnaissance faciale initialisé")

    def load_profile(self, personne_id: int, username: str, embedding: str, password: str = None):
        """
        Charger un profil dans le moteur

        Args:
            personne_id: ID de la personne
            username: Nom d'utilisateur
            embedding: Embedding facial encodé en string
            password: Mot de passe hashé (optionnel)
        """
        try:
            # Décoder l'embedding
            encoding = EncryptionManager.decode_embedding(embedding)
            self.known_encodings.append(encoding)
            self.known_names.append(username)
            self.known_ids.append(personne_id)
            self.known_passwords.append(password)
            logger.log_info(f"Profil chargé: {username} (ID: {personne_id})")
        except Exception as e:
            logger.log_error(f"Erreur lors du chargement du profil {username}: {e}")

    def detect_faces(self, frame: np.ndarray) -> Tuple[List, List]:
        """
        Détecter les visages dans une image

        Args:
            frame: Image à analyser

        Returns:
            Tuple (locations, encodings) où:
            - locations: Liste de tuples (top, right, bottom, left)
            - encodings: Liste d'encodings faciaux
        """
        try:
            # Convertir en RGB si nécessaire
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                rgb_frame = frame[:, :, ::-1]  # BGR to RGB
            else:
                rgb_frame = frame

            # Détecter les visages
            face_locations = face_recognition.face_locations(
                rgb_frame,
                model=FACE_DETECTION_MODEL
            )

            if len(face_locations) == 0:
                return [], []

            # Encoder les visages
            face_encodings = face_recognition.face_encodings(
                rgb_frame,
                face_locations
            )

            logger.log_debug(f"{len(face_locations)} visage(s) détecté(s)")
            return face_locations, face_encodings

        except Exception as e:
            logger.log_error(f"Erreur lors de la détection de visages: {e}")
            return [], []

    def recognize_face(self, face_encoding: np.ndarray) -> Tuple[Optional[int], Optional[str], Optional[str], float]:
        """
        Reconnaître un visage

        Args:
            face_encoding: Encoding facial à comparer

        Returns:
            Tuple (personne_id, username, password, similarity_score)
            Retourne (None, None, None, 0.0) si aucune correspondance
        """
        if len(self.known_encodings) == 0:
            logger.log_warning("Aucun profil chargé pour la reconnaissance")
            return None, None, None, 0.0

        try:
            # Comparer avec les visages connus
            matches = face_recognition.compare_faces(
                self.known_encodings,
                face_encoding,
                tolerance=FACE_RECOGNITION_TOLERANCE
            )

            # Calculer les distances
            face_distances = face_recognition.face_distance(
                self.known_encodings,
                face_encoding
            )

            # Trouver la meilleure correspondance
            if True in matches:
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    personne_id = self.known_ids[best_match_index]
                    username = self.known_names[best_match_index]
                    password = self.known_passwords[best_match_index]
                    similarity_score = 1 - face_distances[best_match_index]

                    # Vérifier si le score dépasse le seuil
                    if similarity_score >= SIMILARITY_THRESHOLD:
                        logger.log_info(f"Visage reconnu: {username} (score: {similarity_score:.2f})")
                        return personne_id, username, password, similarity_score
                    else:
                        logger.log_warning(f"Score insuffisant pour {username}: {similarity_score:.2f}")

            logger.log_info("Aucune correspondance trouvée")
            return None, None, None, 0.0

        except Exception as e:
            logger.log_error(f"Erreur lors de la reconnaissance: {e}")
            return None, None, None, 0.0

    def create_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Créer un encoding à partir d'une image

        Args:
            image: Image contenant un visage

        Returns:
            Encoding facial ou None si aucun visage détecté
        """
        try:
            # Convertir en RGB
            rgb_image = image[:, :, ::-1] if len(image.shape) == 3 else image

            # Détecter et encoder le visage
            encodings = face_recognition.face_encodings(rgb_image)

            if len(encodings) > 0:
                logger.log_info("Encoding créé avec succès")
                return encodings[0]
            else:
                logger.log_warning("Aucun visage détecté dans l'image")
                return None

        except Exception as e:
            logger.log_error(f"Erreur lors de la création de l'encoding: {e}")
            return None

    def compare_encodings(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """
        Comparer deux encodings

        Args:
            encoding1: Premier encoding
            encoding2: Deuxième encoding

        Returns:
            Score de similarité (0 à 1, 1 = identique)
        """
        try:
            distance = face_recognition.face_distance([encoding1], encoding2)[0]
            similarity = 1 - distance
            return similarity
        except Exception as e:
            logger.log_error(f"Erreur lors de la comparaison: {e}")
            return 0.0

    def clear_profiles(self):
        """Effacer tous les profils chargés"""
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.known_passwords = []
        logger.log_info("Tous les profils ont été effacés")

    def get_loaded_profiles_count(self) -> int:
        """Obtenir le nombre de profils chargés"""
        return len(self.known_encodings)

    def is_profile_loaded(self, personne_id: int) -> bool:
        """Vérifier si un profil est chargé"""
        return personne_id in self.known_ids