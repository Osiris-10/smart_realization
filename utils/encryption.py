"""Gestion du chiffrement et hashing des mots de passe"""
import hashlib
import secrets
import base64
from typing import Tuple, Optional
import numpy as np


class EncryptionManager:
    """Classe pour gérer le chiffrement et le hashing"""

    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """
        Hasher un mot de passe avec SHA-256 et un salt

        Args:
            password: Le mot de passe en clair
            salt: Le salt à utiliser (optionnel, généré automatiquement si None)

        Returns:
            Tuple (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # Combiner le mot de passe et le salt
        salted_password = f"{password}{salt}"

        # Hasher avec SHA-256
        hashed = hashlib.sha256(salted_password.encode()).hexdigest()

        return hashed, salt

    @staticmethod
    def hash_password_simple(password: str) -> str:
        """
        Hasher un mot de passe sans salt (pour compatibilité)

        Args:
            password: Le mot de passe en clair

        Returns:
            Hash SHA-256
        """
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hashed: str, salt: str = None) -> bool:
        """
        Vérifier un mot de passe

        Args:
            password: Le mot de passe en clair
            hashed: Le hash stocké
            salt: Le salt utilisé (optionnel)

        Returns:
            True si le mot de passe est correct
        """
        if salt:
            computed_hash, _ = EncryptionManager.hash_password(password, salt)
        else:
            # Compatibilité avec l'ancien système (sans salt)
            computed_hash = EncryptionManager.hash_password_simple(password)

        return computed_hash == hashed

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Générer un token aléatoire sécurisé

        Args:
            length: Longueur du token

        Returns:
            Token aléatoire
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_salt(length: int = 16) -> str:
        """
        Générer un salt aléatoire

        Args:
            length: Longueur du salt

        Returns:
            Salt hexadécimal
        """
        return secrets.token_hex(length)

    @staticmethod
    def encode_embedding(embedding: np.ndarray) -> str:
        """
        Encoder un embedding numpy en string

        Args:
            embedding: Array numpy de l'embedding facial

        Returns:
            String représentant l'embedding
        """
        return ','.join(map(str, embedding.tolist()))

    @staticmethod
    def decode_embedding(embedding_str: str) -> np.ndarray:
        """
        Décoder un embedding string en numpy array

        Args:
            embedding_str: String de l'embedding

        Returns:
            Array numpy
        """
        values = [float(x) for x in embedding_str.split(',')]
        return np.array(values)

    @staticmethod
    def encode_base64(data: bytes) -> str:
        """Encoder des bytes en base64"""
        return base64.b64encode(data).decode('utf-8')

    @staticmethod
    def decode_base64(data: str) -> bytes:
        """Décoder une string base64 en bytes"""
        return base64.b64decode(data.encode('utf-8'))