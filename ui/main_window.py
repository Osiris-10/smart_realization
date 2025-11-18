"""Fenêtre principale de l'application - Mode Utilisateur"""
import tkinter as tk
from tkinter import messagebox, ttk
import cv2
from PIL import Image, ImageTk
from typing import Optional, Callable
from datetime import datetime
from utils.logger import Logger
from config.settings import WINDOW_TITLE, WINDOW_SIZE, COLOR_SUCCESS, COLOR_ERROR
from .camera_widget import CameraWidget
from .auth_dialog import AuthDialog
from .components.status_panel import StatusPanel

logger = Logger()

class MainWindow:
    """Classe pour la fenêtre principale - Mode Utilisateur"""

    def __init__(self, face_engine, auth_manager, antispoof_detector,
                 access_service, user_service, profile_service, db, return_callback=None):
        self.face_engine = face_engine
        self.auth_manager = auth_manager
        self.antispoof_detector = antispoof_detector
        self.access_service = access_service
        self.user_service = user_service
        self.profile_service = profile_service
        self.db = db
        self.return_callback = return_callback  # Callback pour retour au menu principal

        self.root = tk.Tk()
        self.root.title("Mode Utilisateur - " + WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")

        self.camera_widget = None
        self.status_panel = None

        self.current_personne_id = None
        self.face_not_recognized_count = 0
        self.is_paused = False

        # Variables anti-spoofing
        self.antispoofing_active = False
        self.antispoofing_step = 0
        self.blink_detected = False
        self.head_turn_detected = False
        self.antispoofing_passed = False
        self.antispoofing_start_time = None
        self.current_face_location = None

        logger.log_info("Fenêtre utilisateur initialisée")

        # Afficher directement la page d'accueil utilisateur
        self.setup_user_home_page()

    def setup_user_home_page(self):
        """Page d'accueil du mode utilisateur (simplifiée)"""
        # Effacer le contenu existant
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame principal
        main_frame = tk.Frame(self.root, bg='#ECF0F1')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg='#3498DB', height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Titre avec bouton retour
        title_container = tk.Frame(header_frame, bg='#3498DB')
        title_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Bouton retour au menu principal (à gauche)
        if self.return_callback:
            back_btn = tk.Button(
                title_container,
                text="← Menu Principal",
                font=('Arial', 11, 'bold'),
                bg='#2980B9',
                fg='white',
                padx=15,
                pady=8,
                cursor='hand2',
                relief=tk.FLAT,
                command=self.return_to_main_menu
            )
            back_btn.pack(side=tk.LEFT)

        # Titre (centré)
        title_label = tk.Label(
            title_container,
            text="👤 MODE UTILISATEUR",
            font=('Arial', 26, 'bold'),
            bg='#3498DB',
            fg='white'
        )
        title_label.pack(side=tk.LEFT, expand=True)

        # Corps
        body_frame = tk.Frame(main_frame, bg='#ECF0F1')
        body_frame.pack(fill=tk.BOTH, expand=True, pady=50)

        # Sous-titre
        subtitle_label = tk.Label(
            body_frame,
            text="Système de contrôle d'accès par reconnaissance faciale",
            font=('Arial', 14),
            bg='#ECF0F1',
            fg='#7F8C8D'
        )
        subtitle_label.pack(pady=20)

        # Frame des boutons
        buttons_frame = tk.Frame(body_frame, bg='#ECF0F1')
        buttons_frame.pack(pady=40)

        # Bouton démarrer reconnaissance (principal)
        start_button = tk.Button(
            buttons_frame,
            text="▶ DÉMARRER LA RECONNAISSANCE",
            font=('Arial', 18, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=50,
            pady=25,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.show_recognition_page
        )
        start_button.pack(pady=15)

        # Bouton informations
        info_button = tk.Button(
            buttons_frame,
            text="ℹ️ À PROPOS DU SYSTÈME",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            padx=40,
            pady=15,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.show_about
        )
        info_button.pack(pady=10)

        # Info sécurité
        info_frame = tk.Frame(body_frame, bg='#E8F8F5', relief=tk.RAISED, bd=2)
        info_frame.pack(pady=40, padx=120, fill=tk.X)

        info_text = tk.Label(
            info_frame,
            text="🛡️ Processus de vérification sécurisé\n\n"
                 "1. Détection anti-spoofing interactive\n"
                 "2. Reconnaissance faciale automatique\n"
                 "3. Authentification par PIN (si nécessaire)",
            font=('Arial', 11),
            bg='#E8F8F5',
            fg='#16A085',
            justify=tk.LEFT,
            padx=20,
            pady=15
        )
        info_text.pack()

        # Footer
        footer_label = tk.Label(
            main_frame,
            text="© 2025 - Système de Reconnaissance Faciale | Version 1.0",
            font=('Arial', 9),
            bg='#ECF0F1',
            fg='#95A5A6'
        )
        footer_label.pack(side=tk.BOTTOM, pady=10)

    def show_about(self):
        """Afficher les informations sur le système"""
        messagebox.showinfo(
            "À propos du système",
            "🎥 SYSTÈME DE RECONNAISSANCE FACIALE\n"
            "Version 1.0\n\n"
            "Fonctionnalités:\n"
            "• Reconnaissance faciale avancée\n"
            "• Protection anti-spoofing interactive\n"
            "• Authentification multi-facteurs\n"
            "• Traçabilité des accès\n\n"
            "© 2025 - Tous droits réservés"
        )

    def show_recognition_page(self):
        """Afficher la page de reconnaissance"""
        # Effacer le contenu existant
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame gauche (caméra)
        left_frame = tk.Frame(main_frame, bg='black')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame droite (statuts)
        right_frame = tk.Frame(main_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        right_frame.config(width=400)

        # Header avec bouton retour
        header_left = tk.Frame(left_frame, bg='#2C3E50', height=60)
        header_left.pack(fill=tk.X)
        header_left.pack_propagate(False)

        back_button = tk.Button(
            header_left,
            text="← Retour",
            font=('Arial', 11, 'bold'),
            command=self.return_to_user_mode,
            bg='#E74C3C',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        back_button.pack(side=tk.LEFT, padx=10, pady=10)

        title_cam = tk.Label(
            header_left,
            text="🎥 RECONNAISSANCE FACIALE",
            font=('Arial', 14, 'bold'),
            bg='#2C3E50',
            fg='white'
        )
        title_cam.pack(side=tk.LEFT, padx=20)

        # IMPORTANT: Créer le status panel AVANT la caméra
        self.status_panel = StatusPanel(right_frame)

        # Caméra widget (APRÈS le status panel)
        self.camera_widget = CameraWidget(left_frame, self.process_callback)

        # Démarrer la caméra
        if not self.camera_widget.start():
            messagebox.showerror(
                "Erreur Caméra",
                "Impossible de démarrer la caméra!\n\n"
                "Vérifiez que:\n"
                "- Une webcam est connectée\n"
                "- Aucune autre application n'utilise la caméra\n"
                "- Les pilotes de la caméra sont installés"
            )
            self.return_to_user_mode()
            return

        logger.log_info("Page de reconnaissance affichée")

    def process_callback(self, frame):
        """
        Callback pour traiter chaque frame
        Wrapper qui appelle process_frame en gérant les erreurs
        """
        try:
            return self.process_frame(frame)
        except Exception as e:
            logger.log_error(f"Erreur dans process_frame: {e}")
            import traceback
            logger.log_error(traceback.format_exc())
            return frame

    def process_frame(self, frame):
        """
        Traiter chaque frame de la caméra avec anti-spoofing interactif

        Args:
            frame: Image de la caméra

        Returns:
            Frame modifiée avec rectangles et instructions
        """
        # Vérifier que status_panel existe
        if not hasattr(self, 'status_panel') or self.status_panel is None:
            return frame

        if self.is_paused:
            return frame

        # Détecter les visages
        face_locations, face_encodings = self.face_engine.detect_faces(frame)

        if len(face_locations) == 0:
            # Réinitialiser l'anti-spoofing si pas de visage
            if self.antispoofing_active:
                self.reset_antispoofing()
            self.status_panel.update_status("⏳ En attente d'un visage...", "info")
            return frame

        # ... reste du code ...

    def process_antispoofing(self, frame, face_location, face_encoding):
        """Processus anti-spoofing (logique identique)"""
        top, right, bottom, left = face_location
        height, width = frame.shape[:2]

        if not self.antispoofing_active:
            self.antispoofing_active = True
            self.antispoofing_step = 1
            self.antispoofing_start_time = datetime.now()
            self.blink_detected = False
            self.head_turn_detected = False
            logger.log_info("🛡️ Démarrage anti-spoofing")

        cv2.rectangle(frame, (left, top), (right, bottom), (255, 200, 0), 3)

        if self.antispoofing_step == 1:
            # Étape clignement
            instruction_box_height = 120
            cv2.rectangle(frame, (0, 0), (width, instruction_box_height), (50, 50, 50), -1)
            cv2.rectangle(frame, (0, 0), (width, instruction_box_height), (255, 200, 0), 3)

            cv2.putText(frame, "ETAPE 1/2: CLIGNEZ DES YEUX",
                       (int(width/2 - 280), 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(frame, "Clignez plusieurs fois des yeux naturellement",
                       (int(width/2 - 280), 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

            elapsed = (datetime.now() - self.antispoofing_start_time).total_seconds()
            cv2.putText(frame, f"Temps: {int(elapsed)}s",
                       (width - 150, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if not self.blink_detected:
                blink = self.antispoof_detector.detect_blink(frame, face_location)
                if blink:
                    self.blink_detected = True
                    logger.log_info("✅ Clignement détecté!")
                    cv2.putText(frame, "CLIGNEMENT DETECTE!",
                               (int(width/2 - 200), height - 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                    self.root.after(1000, self.next_antispoofing_step)

            status = "✅ Détecté" if self.blink_detected else "⏳ En attente..."
            self.status_panel.update_status(
                f"🛡️ Anti-spoofing: Clignement {status}",
                "success" if self.blink_detected else "info"
            )

        elif self.antispoofing_step == 2:
            # Étape mouvement de tête
            instruction_box_height = 120
            cv2.rectangle(frame, (0, 0), (width, instruction_box_height), (50, 50, 50), -1)
            cv2.rectangle(frame, (0, 0), (width, instruction_box_height), (255, 200, 0), 3)

            cv2.putText(frame, "ETAPE 2/2: TOURNEZ LA TETE",
                       (int(width/2 - 280), 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(frame, "Tournez legerement la tete a gauche puis a droite",
                       (int(width/2 - 320), 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

            cv2.arrowedLine(frame, (100, height//2), (50, height//2), (0, 255, 255), 5, tipLength=0.3)
            cv2.arrowedLine(frame, (width-100, height//2), (width-50, height//2), (0, 255, 255), 5, tipLength=0.3)

            elapsed = (datetime.now() - self.antispoofing_start_time).total_seconds()
            cv2.putText(frame, f"Temps: {int(elapsed)}s",
                       (width - 150, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if not self.head_turn_detected:
                head_turn = self.antispoof_detector.detect_head_turn(frame, face_location)
                if head_turn:
                    self.head_turn_detected = True
                    logger.log_info("✅ Mouvement de tête détecté!")
                    cv2.putText(frame, "MOUVEMENT DETECTE!",
                               (int(width/2 - 200), height - 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                    self.root.after(1000, self.complete_antispoofing)

            status = "✅ Détecté" if self.head_turn_detected else "⏳ En attente..."
            self.status_panel.update_status(
                f"🛡️ Anti-spoofing: Mouvement {status}",
                "success" if self.head_turn_detected else "info"
            )

        # Timeout 30 secondes
        if self.antispoofing_start_time:
            elapsed = (datetime.now() - self.antispoofing_start_time).total_seconds()
            if elapsed > 30:
                logger.log_warning("⏱️ Timeout anti-spoofing")
                self.fail_antispoofing()

        return frame

    def next_antispoofing_step(self):
        """Passer à l'étape suivante"""
        self.antispoofing_step = 2
        logger.log_info("Passage à l'étape 2: Mouvement de tête")

    def complete_antispoofing(self):
        """Compléter l'anti-spoofing"""
        texture_score = 0.8
        liveness_score = self.antispoof_detector.calculate_liveness_score(
            self.blink_detected, self.head_turn_detected, texture_score
        )

        logger.log_info(f"✅ Anti-spoofing réussi! Score: {liveness_score:.2f}")

        if self.antispoof_detector.is_live(liveness_score):
            self.antispoofing_passed = True
            self.antispoofing_active = False

            self.status_panel.update_status(
                f"✅ Anti-spoofing validé! Score: {liveness_score*100:.1f}%",
                "success"
            )

            messagebox.showinfo(
                "✅ Vérification Réussie",
                f"Vous êtes bien une personne réelle!\n\n"
                f"Score de vivacité: {liveness_score*100:.1f}%\n\n"
                f"Reconnaissance faciale en cours..."
            )
        else:
            self.fail_antispoofing()

    def fail_antispoofing(self):
        """Échec anti-spoofing"""
        logger.log_warning("❌ Échec anti-spoofing")
        self.status_panel.update_status("❌ Échec de la vérification anti-spoofing", "error")
        self.access_service.log_access_attempt(None, 'DENIED', 'FACE_ONLY', similarity_score=0.0)

        messagebox.showerror(
            "❌ Vérification Échouée",
            "La vérification anti-spoofing a échouée.\n\n"
            "Raisons possibles:\n"
            "- Utilisation d'une photo ou vidéo\n"
            "- Conditions d'éclairage insuffisantes\n"
            "- Timeout (30 secondes dépassées)\n\n"
            "Veuillez réessayer."
        )

        self.reset_antispoofing()
        self.is_paused = False

    def reset_antispoofing(self):
        """Réinitialiser l'anti-spoofing"""
        self.antispoofing_active = False
        self.antispoofing_step = 0
        self.antispoofing_passed = False
        self.blink_detected = False
        self.head_turn_detected = False
        self.antispoofing_start_time = None
        logger.log_debug("Anti-spoofing réinitialisé")

    def grant_access_direct(self, personne_id, username, similarity):
        """Accorder l'accès directement"""
        self.status_panel.update_status(f"✅ ACCÈS AUTORISÉ: {username}", "success")

        self.access_service.log_access_attempt(
            personne_id, 'GRANTED', 'FACE_ONLY',
            similarity_score=similarity
        )

        self.access_service.log_antispoofing(
            personne_id,
            blink_detected=self.blink_detected,
            headturn_detected=self.head_turn_detected,
            antispoof_score=1.0
        )

        self.access_service.reset_failed_attempts(personne_id)

        logger.log_info(f"✅ Accès autorisé pour {username}")

        messagebox.showinfo(
            "✅ ACCÈS AUTORISÉ",
            f"Bienvenue {username}!\n\n"
            f"✓ Vérification anti-spoofing: RÉUSSIE\n"
            f"✓ Score de reconnaissance: {similarity*100:.1f}%\n\n"
            f"Accès accordé par reconnaissance faciale."
        )

        self.reset_antispoofing()
        self.is_paused = False
        self.face_not_recognized_count = 0

    def request_pin_after_failures(self):
        """Demander le PIN après 3 échecs"""
        dialog = AuthDialog(
            self.root,
            "❌ Reconnaissance échouée (3/3)\n\nEntrez votre mot de passe/PIN pour continuer:"
        )
        password = dialog.get_password()

        if password:
            found = False
            for i, pwd in enumerate(self.face_engine.known_passwords):
                if self.auth_manager.verify_password(password, pwd):
                    personne_id = self.face_engine.known_ids[i]
                    username = self.face_engine.known_names[i]

                    self.status_panel.update_status(f"✅ Accès autorisé: {username} (PIN)", "success")

                    self.access_service.log_access_attempt(personne_id, 'GRANTED', 'PIN_ONLY')
                    self.access_service.reset_failed_attempts(personne_id)
                    self.access_service.increment_failed_attempts(personne_id, 'face')

                    logger.log_info(f"✅ Accès autorisé pour {username} via PIN")

                    messagebox.showinfo(
                        "✅ ACCÈS AUTORISÉ",
                        f"Bienvenue {username}!\n\n"
                        f"Authentification par mot de passe réussie.\n"
                        f"(Reconnaissance faciale échouée)"
                    )
                    found = True
                    break

            if not found:
                self.status_panel.update_status("❌ PIN incorrect", "error")
                self.access_service.log_access_attempt(None, 'DENIED', 'PIN_ONLY')
                logger.log_warning("Échec d'authentification par PIN")
                messagebox.showerror("❌ ACCÈS REFUSÉ", "Mot de passe incorrect!\n\nL'accès est refusé.")

        self.reset_antispoofing()
        self.is_paused = False
        self.face_not_recognized_count = 0

    def return_to_user_home(self):
        """Retourner à la page d'accueil utilisateur"""
        if self.camera_widget:
            self.camera_widget.stop()

        self.reset_antispoofing()
        self.setup_user_home_page()
        logger.log_info("Retour à la page d'accueil utilisateur")

    def return_to_main_menu(self):
        """Retourner au menu principal"""
        if messagebox.askyesno("Retour", "Voulez-vous retourner au menu principal?"):
            if self.camera_widget:
                self.camera_widget.stop()

            self.root.destroy()

            if self.return_callback:
                self.return_callback()

    def run(self):
        """Lancer l'application"""
        try:
            logger.log_info("Lancement de l'interface utilisateur")
            self.root.mainloop()
        except Exception as e:
            logger.log_error(f"Erreur interface: {e}")
        finally:
            if self.camera_widget:
                self.camera_widget.stop()

    def on_closing(self):
        """Gestionnaire de fermeture"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter?"):
            if self.camera_widget:
                self.camera_widget.stop()
            self.root.destroy()