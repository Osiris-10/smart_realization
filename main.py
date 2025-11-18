# main.py
# Navigation améliorée avec retour arrière propre

import sys
import os
from database.connection import DatabaseConnection
from core.face_recognition import FaceRecognitionEngine
from core.authentication import AuthenticationManager
from core.antispoofing import AntiSpoofingDetector
from services.access_service import AccessService
from services.user_service import UserService
from services.profile_service import ProfileService
from ui.main_window import MainWindow
from utils.logger import Logger
import tkinter as tk
from tkinter import messagebox

logger = Logger()


class FaceRecognitionApp:
    """Classe principale de l'application"""

    def __init__(self):
        logger.log_info("=" * 60)
        logger.log_info("DÉMARRAGE DE L'APPLICATION")
        logger.log_info("=" * 60)

        # Créer les dossiers nécessaires
        self.create_directories()

        # Initialiser la base de données
        logger.log_info("Connexion à la base de données...")
        self.db = DatabaseConnection()
        if not self.db.connect():
            logger.log_critical("ERREUR: Impossible de se connecter à la base de données")
            sys.exit(1)

        # Initialiser les services
        logger.log_info("Initialisation des services...")
        self.access_service = AccessService(self.db)
        self.user_service = UserService(self.db)
        self.profile_service = ProfileService(self.db)

        # Initialiser le moteur de reconnaissance
        logger.log_info("Initialisation du moteur de reconnaissance faciale...")
        self.face_engine = FaceRecognitionEngine()
        self.auth_manager = AuthenticationManager()
        self.antispoof_detector = AntiSpoofingDetector()

        # Charger les profils
        self.load_profiles()

        # Fenêtre principale de sélection de mode
        self.root = None

        logger.log_info("Application initialisée avec succès ✓")

    def create_directories(self):
        """Créer les dossiers nécessaires"""
        directories = ['logs', 'temp', 'uploads', 'uploads/faces', 'assets/images', 'assets/sounds']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        logger.log_info("Dossiers créés/vérifiés")

    def load_profiles(self):
        """Charger tous les profils actifs depuis la base de données"""
        logger.log_info("Chargement des profils faciaux...")
        try:
            query = """
                SELECT p.personne_id, p.username, p.password, fp.embedding 
                FROM personne p 
                INNER JOIN face_profiles fp ON p.personne_id = fp.personne_id 
                WHERE p.is_active = TRUE
            """
            results = self.db.execute_query(query)
            if not results:
                logger.log_warning("Aucun profil trouvé dans la base de données")
                return
            for row in results:
                personne_id, username, password, embedding = row
                if embedding:
                    self.face_engine.load_profile(personne_id, username, embedding, password)
            logger.log_info(f"✓ {len(results)} profil(s) chargé(s) avec succès")
        except Exception as e:
            logger.log_error(f"Erreur lors du chargement des profils: {e}")

    def show_startup_menu(self):
        """Afficher le menu de démarrage principal"""
        self.root = tk.Tk()
        self.root.title("Système de Reconnaissance Faciale")
        self.root.geometry("600x500")
        self.root.configure(bg='#2C3E50')

        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2C3E50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Titre
        title = tk.Label(
            main_frame,
            text="🎥 RECONNAISSANCE FACIALE",
            font=('Arial', 28, 'bold'),
            bg='#2C3E50',
            fg='white'
        )
        title.pack(pady=(0, 10))

        subtitle = tk.Label(
            main_frame,
            text="Système de contrôle d'accès sécurisé",
            font=('Arial', 14),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        subtitle.pack(pady=(0, 50))

        # Frame des boutons
        buttons_frame = tk.Frame(main_frame, bg='#2C3E50')
        buttons_frame.pack(pady=30)

        # Bouton Mode Utilisateur
        user_btn = tk.Button(
            buttons_frame,
            text="👤 MODE UTILISATEUR",
            font=('Arial', 16, 'bold'),
            bg='#3498DB',
            fg='white',
            padx=50,
            pady=20,
            cursor='hand2',
            command=self.launch_user_mode
        )
        user_btn.pack(pady=15, fill=tk.X)

        # Bouton Mode Admin
        admin_btn = tk.Button(
            buttons_frame,
            text="🔐 MODE ADMINISTRATEUR",
            font=('Arial', 16, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=50,
            pady=20,
            cursor='hand2',
            command=self.launch_admin_mode
        )
        admin_btn.pack(pady=15, fill=tk.X)

        # Info
        info = tk.Label(
            main_frame,
            text="💡 Sélectionnez un mode pour continuer",
            font=('Arial', 11),
            bg='#2C3E50',
            fg='#95A5A6'
        )
        info.pack(pady=(40, 0))

        # Footer
        footer = tk.Label(
            main_frame,
            text="© 2025 - Système de Reconnaissance Faciale | Version 1.0",
            font=('Arial', 9),
            bg='#2C3E50',
            fg='#7F8C8D'
        )
        footer.pack(side=tk.BOTTOM, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def launch_user_mode(self):
        """Lancer le mode utilisateur"""
        try:
            logger.log_info("Lancement du mode utilisateur...")
            # Cacher la fenêtre de sélection
            self.root.withdraw()

            # Créer la fenêtre utilisateur avec callback de retour
            app = MainWindow(
                face_engine=self.face_engine,
                auth_manager=self.auth_manager,
                antispoof_detector=self.antispoof_detector,
                access_service=self.access_service,
                user_service=self.user_service,
                profile_service=self.profile_service,
                db=self.db,
                return_callback=self.show_main_menu  # Callback pour retour arrière
            )

            app.root.protocol("WM_DELETE_WINDOW", lambda: self.close_user_mode(app))
            app.run()

        except Exception as e:
            logger.log_critical(f"Erreur critique: {e}")
            logger.log_exception("Détails de l'erreur:")
            self.root.deiconify()  # Réafficher le menu en cas d'erreur

    def close_user_mode(self, app):
        """Fermer le mode utilisateur et retourner au menu"""
        if messagebox.askyesno("Quitter", "Voulez-vous retourner au menu principal?"):
            try:
                if app.camera_widget:
                    app.camera_widget.stop()
                app.root.destroy()
            except:
                pass
            self.show_main_menu()

    def launch_admin_mode(self):
        """Lancer le mode administrateur"""
        try:
            logger.log_info("Lancement du mode administrateur...")
            # Cacher la fenêtre de sélection
            self.root.withdraw()

            # Importer AdminWindow
            from ui.admin.admin_window import AdminWindow

            # Créer la fenêtre admin avec callback de retour
            admin_app = AdminWindow(
                db=self.db,
                face_engine=self.face_engine,
                user_service=self.user_service,
                profile_service=self.profile_service,
                access_service=self.access_service,
                return_callback=self.show_main_menu  # Callback pour retour arrière
            )

            # La fenêtre admin gère sa propre boucle mainloop

        except Exception as e:
            logger.log_error(f"Erreur lors du lancement admin: {e}")
            logger.log_exception("Détails:")
            messagebox.showerror("Erreur", f"Impossible de lancer le mode admin: {e}")
            self.show_main_menu()

    def show_main_menu(self):
        """Réafficher le menu principal"""
        try:
            # Détruire l'ancienne fenêtre si elle existe
            if self.root and self.root.winfo_exists():
                try:
                    self.root.deiconify()
                    return
                except:
                    pass

            # Recréer le menu
            self.show_startup_menu()

        except Exception as e:
            logger.log_error(f"Erreur lors de l'affichage du menu: {e}")
            # En dernier recours, recréer complètement
            self.show_startup_menu()

    def on_close(self):
        """Gestionnaire de fermeture de l'application"""
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter l'application?"):
            self.cleanup()
            self.root.destroy()
            sys.exit(0)

    def cleanup(self):
        """Nettoyer les ressources"""
        logger.log_info("Nettoyage des ressources...")
        if self.db:
            self.db.disconnect()
        logger.log_info("=" * 60)
        logger.log_info("APPLICATION FERMÉE")
        logger.log_info("=" * 60)


def main():
    """Point d'entrée principal"""
    try:
        # Bannière
        print("=" * 60)
        print(" SYSTÈME DE RECONNAISSANCE FACIALE ".center(60))
        print(" Version 1.0 ".center(60))
        print("=" * 60)
        print()

        # Créer et lancer l'application
        app = FaceRecognitionApp()
        app.show_startup_menu()

    except KeyboardInterrupt:
        logger.log_info("\nApplication interrompue par l'utilisateur (Ctrl+C)")
        print("\n✓ Application arrêtée proprement")
    except Exception as e:
        logger.log_critical(f"Erreur fatale: {e}")
        logger.log_exception("Traceback complet:")
        print(f"\n✗ ERREUR FATALE: {e}")
        print("Consultez les logs pour plus de détails")
        sys.exit(1)


if __name__ == "__main__":
    main()