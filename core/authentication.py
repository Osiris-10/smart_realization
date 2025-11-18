"""Gestion de l'authentification par mot de passe"""
from typing import Tuple
from utils.encryption import EncryptionManager
from utils.logger import Logger
from config.settings import PASSWORD_LENGTH

logger = Logger()


class AuthenticationManager:
    """Classe pour gérer l'authentification"""

    def __init__(self):
        self.encryption = EncryptionManager()
        logger.log_info("Gestionnaire d'authentification initialisé")

    def verify_password(self, password: str, stored_hash: str, salt: str = None) -> bool:
        """
        Vérifier un mot de passe

        Args:
            password: Mot de passe en clair
            stored_hash: Hash stocké en base
            salt: Salt utilisé (optionnel)

        Returns:
            True si le mot de passe est correct
        """
        try:
            is_valid = self.encryption.verify_password(password, stored_hash, salt)

            if is_valid:
                logger.log_info("Authentification par mot de passe réussie")
            else:
                logger.log_warning("Échec de l'authentification par mot de passe")

            return is_valid

        except Exception as e:
            logger.log_error(f"Erreur lors de la vérification du mot de passe: {e}")
            return False

    def hash_password(self, password: str, use_salt: bool = False) -> Tuple[str, str]:
        """
        Hasher un nouveau mot de passe

        Args:
            password: Mot de passe en clair
            use_salt: Utiliser un salt

        Returns:
            Tuple (hash, salt) ou (hash, None) si pas de salt
        """
        try:
            if use_salt:
                hashed, salt = self.encryption.hash_password(password)
                logger.log_info("Mot de passe hashé avec salt")
                return hashed, salt
            else:
                hashed = self.encryption.hash_password_simple(password)
                logger.log_info("Mot de passe hashé sans salt")
                return hashed, None
        except Exception as e:
            logger.log_error(f"Erreur lors du hashage: {e}")
            return None, None

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Valider la force d'un mot de passe

        Args:
            password: Mot de passe à valider

        Returns:
            Tuple (is_valid, message)
        """
        # Vérifier la longueur minimale
        if len(password) < PASSWORD_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {PASSWORD_LENGTH} caractères"

        # Vérifier qu'il ne contient pas que des chiffres
        if password.isdigit():
            return False, "Le mot de passe ne peut pas contenir uniquement des chiffres"

        # Vérifier qu'il n'est pas vide ou que des espaces
        if not password.strip():
            return False, "Le mot de passe ne peut pas être vide"

        return True, "Mot de passe valide"

    def validate_password_format(self, password: str) -> bool:
        """
        Vérifier le format du mot de passe (pour PIN numérique)

        Args:
            password: Mot de passe à vérifier

        Returns:
            True si le format est correct
        """
        return password.isdigit() and len(password) == PASSWORD_LENGTH

    def generate_secure_password(self, length: int = 12) -> str:
        """
        Générer un mot de passe sécurisé

        Args:
            length: Longueur du mot de passe

        Returns:
            Mot de passe généré
        """
        import string
        import secrets

        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for i in range(length))

        logger.log_info("Mot de passe sécurisé généré")
        return password