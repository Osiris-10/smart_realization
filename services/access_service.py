"""Service de gestion des accès et logs"""
from datetime import datetime
from typing import Optional, List, Tuple
from database.connection import DatabaseConnection
from database.models import AccesLog, AttemptsCounter, AntiSpoofing
from utils.logger import Logger
from config.settings import MAX_FAILED_FACE_ATTEMPTS, MAX_FAILED_PIN_ATTEMPTS

logger = Logger()

class AccessService:
    """Service pour gérer les accès et les logs"""

    def __init__(self, db: DatabaseConnection):
        self.db = db
        logger.log_info("Service d'accès initialisé")

    def log_access_attempt(self, personne_id: Optional[int], access_result: str,
                           access_method: str, image_url: str = None,
                           similarity_score: float = None) -> bool:
        """
        Enregistrer une tentative d'accès

        Args:
            personne_id: ID de la personne (None si non reconnu)
            access_result: 'GRANTED' ou 'DENIED'
            access_method: 'FACE_PIN', 'PIN_ONLY', 'FACE_ONLY'
            image_url: URL de l'image capturée
            similarity_score: Score de similarité faciale

        Returns:
            True si l'enregistrement a réussi
        """
        try:
            # PostgreSQL utilise RETURNING
            query = """
            INSERT INTO acces_log (personne_id, access_result, access_method,
                                  image_url, horaire, similarity_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING access_id
            """

            values = (
                personne_id,
                access_result,
                access_method,
                image_url,
                datetime.now(),
                similarity_score
            )

            access_id = self.db.execute_update(query, values)
            logger.log_info(
                f"Accès enregistré: {access_result} - {access_method} - User: {personne_id} (ID: {access_id})")
            return True

        except Exception as e:
            logger.log_error(f"Erreur enregistrement accès: {e}")
            return False

    def increment_failed_attempts(self, personne_id: int, attempt_type: str) -> bool:
        """
        Incrémenter le compteur d'échecs

        Args:
            personne_id: ID de la personne
            attempt_type: 'face' ou 'pin'

        Returns:
            True si succès
        """
        try:
            # Vérifier si un compteur existe
            query = """
            SELECT counter_id, failed_face_attempts, failed_pin_attempts 
            FROM attempts_counter WHERE personne_id = %s
            """
            result = self.db.execute_query(query, (personne_id,))

            if result:
                counter_id, failed_face, failed_pin = result[0]

                if attempt_type == 'face':
                    failed_face += 1
                else:
                    failed_pin += 1

                update_query = """
                UPDATE attempts_counter
                SET failed_face_attempts = %s, failed_pin_attempts = %s,
                    last_attempt = %s
                WHERE counter_id = %s
                """
                self.db.execute_update(
                    update_query,
                    (failed_face, failed_pin, datetime.now(), counter_id)
                )
            else:
                # Créer un nouveau compteur
                failed_face = 1 if attempt_type == 'face' else 0
                failed_pin = 1 if attempt_type == 'pin' else 0

                insert_query = """
                INSERT INTO attempts_counter 
                (personne_id, failed_face_attempts, failed_pin_attempts, last_attempt)
                VALUES (%s, %s, %s, %s)
                """
                self.db.execute_update(
                    insert_query,
                    (personne_id, failed_face, failed_pin, datetime.now())
                )

            logger.log_info(f"Compteur d'échecs incrémenté pour personne {personne_id} ({attempt_type})")
            return True

        except Exception as e:
            logger.log_error(f"Erreur incrémentation compteur: {e}")
            return False

    def reset_failed_attempts(self, personne_id: int) -> bool:
        """
        Réinitialiser les compteurs d'échecs

        Args:
            personne_id: ID de la personne

        Returns:
            True si succès
        """
        try:
            query = """
            UPDATE attempts_counter
            SET failed_face_attempts = 0, failed_pin_attempts = 0,
                last_attempt = %s
            WHERE personne_id = %s
            """
            self.db.execute_update(query, (datetime.now(), personne_id))
            logger.log_info(f"Compteurs réinitialisés pour personne {personne_id}")
            return True

        except Exception as e:
            logger.log_error(f"Erreur réinitialisation compteurs: {e}")
            return False

    def get_failed_attempts(self, personne_id: int) -> Tuple[int, int]:
        """
        Récupérer les compteurs d'échecs

        Args:
            personne_id: ID de la personne

        Returns:
            Tuple (failed_face_attempts, failed_pin_attempts)
        """
        try:
            query = """
            SELECT failed_face_attempts, failed_pin_attempts
            FROM attempts_counter WHERE personne_id = %s
            """
            result = self.db.execute_query(query, (personne_id,))

            if result:
                return result[0]
            return 0, 0

        except Exception as e:
            logger.log_error(f"Erreur récupération compteurs: {e}")
            return 0, 0

    def is_locked_out(self, personne_id: int) -> bool:
        """
        Vérifier si un utilisateur est bloqué

        Args:
            personne_id: ID de la personne

        Returns:
            True si bloqué
        """
        face_attempts, pin_attempts = self.get_failed_attempts(personne_id)

        is_locked = (face_attempts >= MAX_FAILED_FACE_ATTEMPTS or
                     pin_attempts >= MAX_FAILED_PIN_ATTEMPTS)

        if is_locked:
            logger.log_warning(f"Utilisateur {personne_id} est bloqué")

        return is_locked

    def log_antispoofing(self, personne_id: int, blink_detected: bool,
                         headturn_detected: bool, antispoof_score: float) -> bool:
        """
        Enregistrer les résultats d'anti-spoofing

        Args:
            personne_id: ID de la personne
            blink_detected: Clignement détecté
            headturn_detected: Mouvement de tête détecté
            antispoof_score: Score global

        Returns:
            True si succès
        """
        try:
            query = """
            INSERT INTO antispoofing 
            (personne_id, blink_detected, headturn_detected, antispoof_score, jour, horaire)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING antispoof_id
            """

            values = (
                personne_id,
                blink_detected,
                headturn_detected,
                antispoof_score,
                datetime.now().date(),
                datetime.now()
            )

            antispoof_id = self.db.execute_update(query, values)
            logger.log_info(f"Anti-spoofing enregistré pour personne {personne_id} (ID: {antispoof_id})")
            return True

        except Exception as e:
            logger.log_error(f"Erreur enregistrement anti-spoofing: {e}")
            return False

    def get_access_history(self, personne_id: int, limit: int = 10) -> List[AccesLog]:
        """
        Récupérer l'historique d'accès d'une personne

        Args:
            personne_id: ID de la personne
            limit: Nombre maximum de résultats

        Returns:
            Liste d'objets AccesLog
        """
        try:
            query = """
            SELECT * FROM acces_log
            WHERE personne_id = %s
            ORDER BY horaire DESC
            LIMIT %s
            """

            results = self.db.execute_query(query, (personne_id, limit))

            access_logs = []
            for row in results:
                access_logs.append(AccesLog.from_db_row(row))

            return access_logs

        except Exception as e:
            logger.log_error(f"Erreur récupération historique: {e}")
            return []

    def get_all_access_logs(self, limit: int = 50) -> List[AccesLog]:
        """Récupérer tous les logs d'accès récents"""
        try:
            query = """
            SELECT * FROM acces_log
            ORDER BY horaire DESC
            LIMIT %s
            """

            results = self.db.execute_query(query, (limit,))

            access_logs = []
            for row in results:
                access_logs.append(AccesLog.from_db_row(row))

            return access_logs

        except Exception as e:
            logger.log_error(f"Erreur récupération logs: {e}")
            return []