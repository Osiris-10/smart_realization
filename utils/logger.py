"""Système de logging pour l'application"""
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_FORMAT


class Logger:
    """Classe singleton pour gérer les logs de l'application"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # Créer le dossier logs s'il n'existe pas
        os.makedirs('logs', exist_ok=True)

        # Configuration du logger principal
        self.logger = logging.getLogger('FaceRecognitionSystem')
        self.logger.setLevel(getattr(logging, LOG_LEVEL))

        # Éviter la duplication des handlers
        if not self.logger.handlers:
            # Format des logs
            formatter = logging.Formatter(
                LOG_FORMAT,
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # Handler pour fichier avec rotation
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Handler pour console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_info(self, message: str):
        """Logger un message d'information"""
        self.logger.info(message)

    def log_error(self, message: str):
        """Logger une erreur"""
        self.logger.error(message)

    def log_warning(self, message: str):
        """Logger un avertissement"""
        self.logger.warning(message)

    def log_debug(self, message: str):
        """Logger un message de debug"""
        self.logger.debug(message)

    def log_critical(self, message: str):
        """Logger un message critique"""
        self.logger.critical(message)

    def log_exception(self, message: str):
        """Logger une exception avec traceback"""
        self.logger.exception(message)