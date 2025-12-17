"""Moteur de reconnaissance faciale - OPTIMISÉ ET FIABLE"""
import face_recognition
import numpy as np
import cv2
from typing import List, Tuple, Optional
from config.settings import FACE_RECOGNITION_TOLERANCE, SIMILARITY_THRESHOLD
from utils.logger import Logger
from utils.encryption import EncryptionManager

logger = Logger()


class FaceRecognitionEngine:
    """Moteur optimisé pour performances ET fiabilité"""

    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.known_passwords = []
        self.frame_skip_counter = 0
        logger.log_info("✅ Moteur optimisé initialisé")

    def load_profile(self, personne_id: int, username: str, embedding: str, password: str = None):
        """Charger un profil"""
        try:
            encoding = EncryptionManager.decode_embedding(embedding)
            self.known_encodings.append(encoding)
            self.known_names.append(username)
            self.known_ids.append(personne_id)
            self.known_passwords.append(password)
            logger.log_info(f"✅ Profil chargé: {username}")
        except Exception as e:
            logger.log_error(f"❌ Erreur chargement profil: {e}")

    def detect_faces(self, frame: np.ndarray) -> Tuple[List, List]:
        """Détecter les visages - VERSION ULTRA-ROBUSTE"""
        try:
            # ✅ NE PAS SKIP DE FRAMES pour maximiser la détection
            h, w, c = frame.shape

            # ✅ AMÉLIORER LE CONTRASTE avant détection (CRITIQUE pour faible éclairage)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced_frame = cv2.merge([l, a, b])
            enhanced_frame = cv2.cvtColor(enhanced_frame, cv2.COLOR_LAB2BGR)

            # ✅ TENTATIVE 1 : Détection sur frame ORIGINALE (sans réduction)
            rgb_full = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)

            face_locations = []
            try:
                face_locations = face_recognition.face_locations(
                    rgb_full,
                    model='hog',
                    number_of_times_to_upsample=2  # ← AUGMENTÉ à 2 pour meilleure détection
                )
                logger.log_debug(f"Tentative 1 (full): {len(face_locations)} visage(s)")
            except Exception as e:
                logger.log_debug(f"Tentative 1 échouée: {e}")

            # ✅ TENTATIVE 2 : Si échec, essayer avec réduction légère (85%)
            if len(face_locations) == 0:
                try:
                    small_frame = cv2.resize(rgb_full, (0, 0), fx=0.85, fy=0.85)
                    face_locations_small = face_recognition.face_locations(
                        small_frame,
                        model='hog',
                        number_of_times_to_upsample=2
                    )

                    # Rescale les positions
                    scale_factor = 1 / 0.85
                    face_locations = [
                        (int(top * scale_factor),
                         int(right * scale_factor),
                         int(bottom * scale_factor),
                         int(left * scale_factor))
                        for (top, right, bottom, left) in face_locations_small
                    ]
                    logger.log_debug(f"Tentative 2 (85%): {len(face_locations)} visage(s)")
                except Exception as e:
                    logger.log_debug(f"Tentative 2 échouée: {e}")

            # ✅ TENTATIVE 3 : Utiliser OpenCV Haar Cascade en dernier recours
            if len(face_locations) == 0:
                try:
                    gray = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2GRAY)
                    face_cascade = cv2.CascadeClassifier(
                        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    )
                    faces = face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(60, 60)
                    )

                    # Convertir format OpenCV (x,y,w,h) vers format dlib (top,right,bottom,left)
                    face_locations = [
                        (y, x + w, y + h, x)
                        for (x, y, w, h) in faces
                    ]
                    logger.log_debug(f"Tentative 3 (Haar): {len(face_locations)} visage(s)")
                except Exception as e:
                    logger.log_debug(f"Tentative 3 échouée: {e}")

            # Aucun visage trouvé
            if len(face_locations) == 0:
                return [], []

            logger.log_info(f"✅ {len(face_locations)} visage(s) détecté(s)")

            # ✅ ENCODER sur frame originale (non modifiée pour précision)
            try:
                rgb_original = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(
                    rgb_original,
                    face_locations,
                    num_jitters=1,
                    model='large'
                )

                return face_locations, face_encodings

            except Exception as e:
                logger.log_error(f"❌ Erreur encodage: {e}")
                return face_locations, []

        except Exception as e:
            logger.log_error(f"❌ Erreur générale détection: {e}")
            import traceback
            logger.log_error(traceback.format_exc())
            return [], []

    def recognize_face(self, face_encoding: np.ndarray) -> Tuple[Optional[int], Optional[str], Optional[str], float]:
        """Reconnaître un visage"""
        if len(self.known_encodings) == 0:
            return None, None, None, 0.0

        try:
            # Comparer avec tolérance
            matches = face_recognition.compare_faces(
                self.known_encodings,
                face_encoding,
                tolerance=FACE_RECOGNITION_TOLERANCE
            )

            face_distances = face_recognition.face_distance(
                self.known_encodings,
                face_encoding
            )

            if True in matches:
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    personne_id = self.known_ids[best_match_index]
                    username = self.known_names[best_match_index]
                    password = self.known_passwords[best_match_index]
                    similarity_score = 1 - face_distances[best_match_index]

                    if similarity_score >= SIMILARITY_THRESHOLD:
                        logger.log_info(f"✅ RECONNU: {username} (similarité: {similarity_score:.2%})")
                        return personne_id, username, password, similarity_score

            logger.log_debug(f"Visage détecté mais non reconnu (meilleur score: {1 - min(face_distances):.2%})")
            return None, None, None, 0.0

        except Exception as e:
            logger.log_error(f"❌ Erreur reconnaissance: {e}")
            return None, None, None, 0.0

    def create_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Créer un encoding à partir d'une image"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_image, model='hog')

            if len(locations) > 0:
                encodings = face_recognition.face_encodings(
                    rgb_image,
                    locations,
                    num_jitters=2  # Plus précis pour l'enregistrement
                )
                if len(encodings) > 0:
                    logger.log_info("✅ Encoding créé avec succès")
                    return encodings[0]

            logger.log_warning("❌ Aucun visage détecté dans l'image")
            return None

        except Exception as e:
            logger.log_error(f"❌ Erreur création encoding: {e}")
            return None

    def compare_encodings(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Comparer deux encodings"""
        try:
            distance = face_recognition.face_distance([encoding1], encoding2)[0]
            return 1 - distance
        except Exception as e:
            logger.log_error(f"❌ Erreur comparaison: {e}")
            return 0.0

    def clear_profiles(self):
        """Effacer tous les profils chargés"""
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.known_passwords = []
        self.frame_skip_counter = 0
        logger.log_info("✅ Profils effacés")

    def get_loaded_profiles_count(self) -> int:
        """Obtenir le nombre de profils chargés"""
        return len(self.known_encodings)

    def is_profile_loaded(self, personne_id: int) -> bool:
        """Vérifier si un profil est chargé"""
        return personne_id in self.known_ids