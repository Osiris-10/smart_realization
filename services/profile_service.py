"""Service de gestion des profils faciaux"""
from typing import Optional, List
from database.connection import DatabaseConnection
from database.models import FaceProfile
from utils.logger import Logger
from utils.encryption import EncryptionManager
import numpy as np

logger = Logger()


class ProfileService:
    """Service pour gérer les profils faciaux"""

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.encryption = EncryptionManager()
        logger.log_info("Service de profils initialisé")

    def create_profile(self, personne_id: int, embedding: np.ndarray,
                       image_url: str = None) -> Optional[int]:
        """
        Créer un profil facial

        Args:
            personne_id: ID de la personne
            embedding: Encoding facial (numpy array)
            image_url: URL ou chemin de l'image

        Returns:
            ID du profil créé ou None
        """
        try:
            # Vérifier si un profil existe déjà
            existing_profile = self.get_profile_by_user(personne_id)
            if existing_profile:
                logger.log_warning(f"Un profil existe déjà pour personne {personne_id}")
                return None

            # Encoder l'embedding
            embedding_str = self.encryption.encode_embedding(embedding)

            # PostgreSQL utilise RETURNING
            query = """
            INSERT INTO face_profiles (personne_id, embedding, image_url)
            VALUES (%s, %s, %s)
            RETURNING profile_id
            """

            profile_id = self.db.execute_update(query, (personne_id, embedding_str, image_url))
            logger.log_info(f"Profil créé pour personne {personne_id} (Profile ID: {profile_id})")
            return profile_id

        except Exception as e:
            logger.log_error(f"Erreur création profil: {e}")
            return None

    def get_profile_by_id(self, profile_id: int) -> Optional[FaceProfile]:
        """
        Récupérer un profil par son ID

        Args:
            profile_id: ID du profil

        Returns:
            Objet FaceProfile ou None
        """
        try:
            query = "SELECT * FROM face_profiles WHERE profile_id = %s"
            result = self.db.execute_query(query, (profile_id,))

            if result:
                return FaceProfile.from_db_row(result[0])
            return None

        except Exception as e:
            logger.log_error(f"Erreur récupération profil: {e}")
            return None

    def get_profile_by_user(self, personne_id: int) -> Optional[FaceProfile]:
        """
        Récupérer le profil d'un utilisateur

        Args:
            personne_id: ID de la personne

        Returns:
            Objet FaceProfile ou None
        """
        try:
            query = "SELECT * FROM face_profiles WHERE personne_id = %s"
            result = self.db.execute_query(query, (personne_id,))

            if result:
                return FaceProfile.from_db_row(result[0])
            return None

        except Exception as e:
            logger.log_error(f"Erreur récupération profil: {e}")
            return None

    def update_profile(self, profile_id: int, embedding: np.ndarray = None,
                       image_url: str = None) -> bool:
        """
        Mettre à jour un profil

        Args:
            profile_id: ID du profil
            embedding: Nouvel embedding (optionnel)
            image_url: Nouvelle URL d'image (optionnel)

        Returns:
            True si succès
        """
        try:
            fields = []
            values = []

            if embedding is not None:
                embedding_str = self.encryption.encode_embedding(embedding)
                fields.append("embedding = %s")
                values.append(embedding_str)

            if image_url is not None:
                fields.append("image_url = %s")
                values.append(image_url)

            if not fields:
                logger.log_warning("Aucun champ à mettre à jour")
                return False

            # Ajouter updated_at
            fields.append("updated_at = NOW()")
            values.append(profile_id)

            query = f"UPDATE face_profiles SET {', '.join(fields)} WHERE profile_id = %s"
            self.db.execute_update(query, tuple(values))

            logger.log_info(f"Profil {profile_id} mis à jour")
            return True

        except Exception as e:
            logger.log_error(f"Erreur mise à jour profil: {e}")
            return False

    def delete_profile(self, profile_id: int) -> bool:
        """
        Supprimer un profil

        Args:
            profile_id: ID du profil

        Returns:
            True si succès
        """
        try:
            query = "DELETE FROM face_profiles WHERE profile_id = %s"
            self.db.execute_update(query, (profile_id,))
            logger.log_info(f"Profil {profile_id} supprimé")
            return True

        except Exception as e:
            logger.log_error(f"Erreur suppression profil: {e}")
            return False

    def delete_profile_by_user(self, personne_id: int) -> bool:
        """Supprimer le profil d'un utilisateur"""
        try:
            query = "DELETE FROM face_profiles WHERE personne_id = %s"
            self.db.execute_update(query, (personne_id,))
            logger.log_info(f"Profil supprimé pour personne {personne_id}")
            return True

        except Exception as e:
            logger.log_error(f"Erreur suppression profil: {e}")
            return False

    def get_all_profiles(self) -> List[FaceProfile]:
        """Récupérer tous les profils"""
        try:
            query = "SELECT * FROM face_profiles ORDER BY created_at DESC"
            results = self.db.execute_query(query)

            profiles = []
            for row in results:
                profiles.append(FaceProfile.from_db_row(row))

            return profiles

        except Exception as e:
            logger.log_error(f"Erreur récupération profils: {e}")
            return []

    def profile_exists(self, personne_id: int) -> bool:
        """Vérifier si un profil existe pour un utilisateur"""
        return self.get_profile_by_user(personne_id) is not None

    def get_profiles_with_users(self) -> List[dict]:
        """
        Récupérer tous les profils avec les informations utilisateur

        Returns:
            Liste de dictionnaires contenant profil + utilisateur
        """
        try:
            query = """
            SELECT fp.profile_id, fp.personne_id, fp.embedding, fp.image_url,
                   p.username, p.email, p.role, p.is_active
            FROM face_profiles fp
            INNER JOIN personne p ON fp.personne_id = p.personne_id
            ORDER BY p.username
            """

            results = self.db.execute_query(query)

            profiles_data = []
            for row in results:
                profiles_data.append({
                    'profile_id': row[0],
                    'personne_id': row[1],
                    'embedding': row[2],
                    'image_url': row[3],
                    'username': row[4],
                    'email': row[5],
                    'role': row[6],
                    'is_active': row[7]
                })

            return profiles_data

        except Exception as e:
            logger.log_error(f"Erreur récupération profils avec utilisateurs: {e}")
            return []