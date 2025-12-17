"""Service de gestion des utilisateurs"""
from datetime import datetime
from typing import Optional, List
from database.connection import DatabaseConnection
from database.models import Personne
from utils.logger import Logger
from core.authentication import AuthenticationManager

logger = Logger()


class UserService:
    """Service pour gérer les utilisateurs"""

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.auth_manager = AuthenticationManager()
        logger.log_info("Service utilisateur initialisé")

    def get_user_by_id(self, personne_id: int) -> Optional[Personne]:
        """
        Récupérer un utilisateur par son ID

        Args:
            personne_id: ID de la personne

        Returns:
            Objet Personne ou None
        """
        try:
            query = "SELECT * FROM personne WHERE personne_id = %s"
            result = self.db.execute_query(query, (personne_id,))

            if result:
                return Personne.from_db_row(result[0])
            return None

        except Exception as e:
            logger.log_error(f"Erreur récupération utilisateur: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Personne]:
        """
        Récupérer un utilisateur par son nom

        Args:
            username: Nom d'utilisateur

        Returns:
            Objet Personne ou None
        """
        try:
            query = "SELECT * FROM personne WHERE username = %s"
            result = self.db.execute_query(query, (username,))

            if result:
                return Personne.from_db_row(result[0])
            return None

        except Exception as e:
            logger.log_error(f"Erreur récupération utilisateur: {e}")
            return None

    def create_user(self, username: str, password: str, email: str,
                    role: str = 'USER') -> Optional[int]:
        """
        Créer un nouvel utilisateur

        Args:
            username: Nom d'utilisateur
            password: Mot de passe en clair
            email: Adresse email
            role: Rôle ('USER', 'ADMIN', 'GUEST')

        Returns:
            ID de la personne créée ou None
        """
        try:
            # Vérifier si l'utilisateur existe déjà
            if self.get_user_by_username(username):
                logger.log_warning(f"L'utilisateur {username} existe déjà")
                return None

            # Hasher le mot de passe
            hashed_password, salt = self.auth_manager.hash_password(password, use_salt=False)

            # PostgreSQL utilise RETURNING pour récupérer l'ID
            query = """
            INSERT INTO personne (username, password, email, role, created_at, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING personne_id
            """

            values = (username, hashed_password, email, role, datetime.now(), True)

            personne_id = self.db.execute_update(query, values)
            logger.log_info(f"Utilisateur créé: {username} (ID: {personne_id})")
            return personne_id

        except Exception as e:
            logger.log_error(f"Erreur création utilisateur: {e}")
            return None

    def update_user(self, personne_id: int, **kwargs) -> bool:
        """
        Mettre à jour un utilisateur

        Args:
            personne_id: ID de la personne
            **kwargs: Champs à mettre à jour (username, email, role, etc.)

        Returns:
            True si succès
        """
        try:
            print("\n>>> SERVICE update_user() APPELÉ")
            
            # Construire la requête dynamiquement
            fields = []
            values = []

            for key, value in kwargs.items():
                if key in ['username', 'email', 'role', 'is_active']:
                    fields.append(f"{key} = %s")
                    values.append(value)
                    print(f"  Champ ajouté: {key} = {value}")
                elif key == 'password' and value:
                    hashed, _ = self.auth_manager.hash_password(value, use_salt=False)
                    fields.append("password = %s")
                    values.append(hashed)
                    print(f"  Champ ajouté: password = (hashé)")

            if not fields:
                print("  ❌ Aucun champ à mettre à jour!")
                return False

            values.append(personne_id)

            query = f"UPDATE personne SET {', '.join(fields)} WHERE personne_id = %s"
            print(f"\n  SQL: {query}")
            print(f"  Valeurs: {[v if k != 'password' else '****' for k, v in zip(list(kwargs.keys()) + ['id'], values)]}")
            
            result = self.db.execute_update(query, tuple(values))
            print(f"  Lignes affectées: {result}")

            if result and result > 0:
                print(f"  ✅ Mise à jour réussie!")
                return True
            else:
                print(f"  ⚠️ Aucune ligne affectée (result={result})")
                return True  # Retourner True quand même car pas d'erreur

        except Exception as e:
            logger.log_error(f"Erreur mise à jour utilisateur: {e}")
            import traceback
            logger.log_error(traceback.format_exc())
            return False

    def deactivate_user(self, personne_id: int) -> bool:
        """
        Désactiver un utilisateur

        Args:
            personne_id: ID de la personne

        Returns:
            True si succès
        """
        try:
            query = "UPDATE personne SET is_active = FALSE WHERE personne_id = %s"
            self.db.execute_update(query, (personne_id,))
            logger.log_info(f"Utilisateur {personne_id} désactivé")
            return True

        except Exception as e:
            logger.log_error(f"Erreur désactivation utilisateur: {e}")
            return False

    def activate_user(self, personne_id: int) -> bool:
        """Activer un utilisateur"""
        try:
            query = "UPDATE personne SET is_active = TRUE WHERE personne_id = %s"
            self.db.execute_update(query, (personne_id,))
            logger.log_info(f"Utilisateur {personne_id} activé")
            return True

        except Exception as e:
            logger.log_error(f"Erreur activation utilisateur: {e}")
            return False

    def delete_user(self, personne_id: int) -> bool:
        """
        Supprimer un utilisateur (suppression physique)

        Args:
            personne_id: ID de la personne

        Returns:
            True si succès
        """
        try:
            query = "DELETE FROM personne WHERE personne_id = %s"
            self.db.execute_update(query, (personne_id,))
            logger.log_info(f"Utilisateur {personne_id} supprimé")
            return True

        except Exception as e:
            logger.log_error(f"Erreur suppression utilisateur: {e}")
            return False

    def get_all_users(self, where_clause: str = "", params: tuple = ()) -> List[Personne]:
        """Récupérer tous les utilisateurs avec filtre optionnel (params sécurisés)"""
        try:
            base_query = "SELECT * FROM personne"
            order_part = " ORDER BY created_at DESC"
            
            if where_clause:
                query = f"{base_query} {where_clause}{order_part}"
            else:
                query = f"{base_query}{order_part}"
            
            logger.log_info(f"Query: {query}")
            logger.log_info(f"Params: {params}")
            
            # Exécuter avec ou sans paramètres
            if params:
                results = self.db.execute_query(query, params)
            else:
                results = self.db.execute_query(query)

            logger.log_info(f"Résultats: {len(results) if results else 0} lignes")

            users = []
            if results:
                for row in results:
                    users.append(Personne.from_db_row(row))

            return users

        except Exception as e:
            logger.log_error(f"Erreur récupération utilisateurs: {e}")
            import traceback
            logger.log_error(traceback.format_exc())
            return []

    def get_all_active_users(self) -> List[Personne]:
        """Récupérer tous les utilisateurs actifs"""
        try:
            query = "SELECT * FROM personne WHERE is_active = TRUE ORDER BY username"
            results = self.db.execute_query(query)

            users = []
            for row in results:
                users.append(Personne.from_db_row(row))

            return users

        except Exception as e:
            logger.log_error(f"Erreur récupération utilisateurs actifs: {e}")
            return []

    def user_exists(self, username: str) -> bool:
        """Vérifier si un utilisateur existe"""
        return self.get_user_by_username(username) is not None

    def get_user_count(self) -> int:
        """Obtenir le nombre total d'utilisateurs"""
        try:
            query = "SELECT COUNT(*) FROM personne"
            result = self.db.execute_query(query)
            return result[0][0] if result else 0
        except Exception as e:
            logger.log_error(f"Erreur comptage utilisateurs: {e}")
            return 0