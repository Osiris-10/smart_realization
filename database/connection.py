"""Gestion de la connexion à la base de données PostgreSQL"""
import psycopg2
from psycopg2 import Error, pool
from psycopg2.extras import RealDictCursor
from typing import List, Tuple, Optional, Any
from config.database import DB_CONFIG
from utils.logger import Logger

logger = Logger()

class DatabaseConnection:
    """Classe singleton pour gérer la connexion à PostgreSQL"""

    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.connection = None
        self.cursor = None
        self._setup_pool()

    def _setup_pool(self):
        """Configurer le pool de connexions"""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                options=DB_CONFIG.get('options', '')
            )
            logger.log_info("Pool de connexions PostgreSQL créé avec succès")
        except Error as e:
            logger.log_error(f"Erreur création du pool: {e}")

    def connect(self) -> bool:
        """Établir la connexion à la base de données"""
        try:
            if self._pool:
                self.connection = self._pool.getconn()
            else:
                self.connection = psycopg2.connect(
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    database=DB_CONFIG['database'],
                    options=DB_CONFIG.get('options', '')
                )

            if self.connection:
                self.cursor = self.connection.cursor()
                # Récupérer la version PostgreSQL
                self.cursor.execute("SELECT version();")
                db_info = self.cursor.fetchone()[0]
                logger.log_info(f"Connecté à PostgreSQL: {db_info}")
                return True
            return False

        except Error as e:
            logger.log_error(f"Erreur de connexion à la base de données: {e}")
            return False

    def disconnect(self):
        """Fermer la connexion à la base de données"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None

            if self.connection:
                if self._pool:
                    self._pool.putconn(self.connection)
                else:
                    self.connection.close()
                self.connection = None
                logger.log_info("Connexion à la base de données fermée")
        except Error as e:
            logger.log_error(f"Erreur lors de la fermeture: {e}")

    def execute_query(self, query: str, params: Tuple = None) -> Optional[List[Tuple]]:
        """
        Exécuter une requête SELECT

        Args:
            query: Requête SQL
            params: Paramètres de la requête

        Returns:
            Liste de tuples avec les résultats
        """
        try:
            if not self.cursor:
                logger.log_error("Pas de curseur actif")
                return None

            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            results = self.cursor.fetchall()
            logger.log_debug(f"Requête exécutée: {self.cursor.rowcount} ligne(s)")
            return results

        except Error as e:
            logger.log_error(f"Erreur lors de l'exécution de la requête: {e}")
            return None

    def execute_update(self, query: str, params: Tuple = None) -> Optional[int]:
        """
        Exécuter une requête INSERT/UPDATE/DELETE

        Args:
            query: Requête SQL
            params: Paramètres de la requête

        Returns:
            ID de la dernière ligne insérée ou nombre de lignes affectées
        """
        try:
            if not self.cursor:
                logger.log_error("Pas de curseur actif")
                return None

            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            self.connection.commit()

            # Pour INSERT avec RETURNING, récupérer l'ID
            if query.strip().upper().startswith('INSERT') and 'RETURNING' in query.upper():
                result = self.cursor.fetchone()
                if result:
                    logger.log_debug(f"Insertion effectuée: ID {result[0]}")
                    return result[0]

            # Pour UPDATE/DELETE, retourner le nombre de lignes affectées
            result = self.cursor.rowcount
            logger.log_debug(f"Mise à jour effectuée: {result} ligne(s)")
            return result

        except Error as e:
            logger.log_error(f"Erreur lors de la mise à jour: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def execute_many(self, query: str, data: List[Tuple]) -> bool:
        """
        Exécuter plusieurs requêtes en batch

        Args:
            query: Requête SQL
            data: Liste de tuples de paramètres

        Returns:
            True si succès
        """
        try:
            if not self.cursor:
                logger.log_error("Pas de curseur actif")
                return False

            self.cursor.executemany(query, data)
            self.connection.commit()
            logger.log_info(f"Batch exécuté: {len(data)} ligne(s)")
            return True

        except Error as e:
            logger.log_error(f"Erreur lors de l'exécution batch: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def begin_transaction(self):
        """Démarrer une transaction"""
        try:
            if self.connection:
                # PostgreSQL démarre automatiquement une transaction
                logger.log_debug("Transaction démarrée")
        except Error as e:
            logger.log_error(f"Erreur début transaction: {e}")

    def commit(self):
        """Valider la transaction"""
        try:
            if self.connection:
                self.connection.commit()
                logger.log_debug("Transaction validée")
        except Error as e:
            logger.log_error(f"Erreur commit: {e}")

    def rollback(self):
        """Annuler la transaction"""
        try:
            if self.connection:
                self.connection.rollback()
                logger.log_debug("Transaction annulée")
        except Error as e:
            logger.log_error(f"Erreur rollback: {e}")

    def execute_script(self, script: str) -> bool:
        """Exécuter un script SQL (multiple statements)"""
        try:
            if not self.cursor:
                logger.log_error("Pas de curseur actif")
                return False

            self.cursor.execute(script)
            self.connection.commit()
            logger.log_info("Script SQL exécuté avec succès")
            return True

        except Error as e:
            logger.log_error(f"Erreur lors de l'exécution du script: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def table_exists(self, table_name: str) -> bool:
        """Vérifier si une table existe"""
        try:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """
            result = self.execute_query(query, (table_name,))
            return result is not None and result[0][0]
        except Exception as e:
            logger.log_error(f"Erreur vérification table: {e}")
            return False

    def __enter__(self):
        """Support du context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fermeture automatique de la connexion"""
        if exc_type:
            self.rollback()
        self.disconnect()

    def __del__(self):
        """Destructeur"""
        self.disconnect()