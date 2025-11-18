"""Script pour créer le premier compte administrateur"""

from database.connection import DatabaseConnection
from services.user_service import UserService
from utils.logger import Logger
from datetime import datetime  # ← AJOUTER

logger = Logger()

# ... reste du code identique ...


def create_initial_admin():
    """Créer le premier compte administrateur"""
    print("=" * 60)
    print(" CRÉATION DU COMPTE ADMINISTRATEUR INITIAL")
    print("=" * 60)
    print()

    # Connexion à la base
    db = DatabaseConnection()
    if not db.connect():
        print("❌ Erreur: Impossible de se connecter à la base de données")
        return

    user_service = UserService(db)

    # Demander les informations
    username = input("Nom d'utilisateur admin: ").strip()

    if user_service.user_exists(username):
        print(f"❌ L'utilisateur '{username}' existe déjà!")
        db.disconnect()
        return

    password = input("Mot de passe: ").strip()
    email = input("Email (optionnel): ").strip()

    # Créer l'admin
    try:
        admin_id = user_service.create_user(
            username=username,
            password=password,
            email=email if email else None,
            role='ADMIN'
        )

        if admin_id:
            print()
            print("=" * 60)
            print("✅ COMPTE ADMINISTRATEUR CRÉÉ AVEC SUCCÈS!")
            print("=" * 60)
            print(f"ID: {admin_id}")
            print(f"Username: {username}")
            print(f"Rôle: ADMIN")
            print()
            print("Vous pouvez maintenant vous connecter via l'espace admin.")
            logger.log_info(f"Compte admin créé: {username} (ID: {admin_id})")
        else:
            print("❌ Erreur lors de la création du compte")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        logger.log_error(f"Erreur création admin: {e}")

    finally:
        db.disconnect()


if __name__ == "__main__":
    create_initial_admin()