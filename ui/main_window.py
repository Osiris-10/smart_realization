"""Fenêtre principale de l'application - Mode Utilisateur"""
import tkinter as tk
from tkinter import messagebox, ttk
import cv2
from PIL import Image, ImageTk
from typing import Optional, Callable
from datetime import datetime
import os
import threading
from utils.logger import Logger
from config.settings import WINDOW_TITLE, WINDOW_SIZE, COLOR_SUCCESS, COLOR_ERROR
from .camera_widget import CameraWidget
from .auth_dialog import AuthDialog
from .components.status_panel import StatusPanel
from services.email_service import send_security_alert
from services.arduino_service import signal_access_granted, signal_access_denied, init_arduino

logger = Logger()

# Dossier pour stocker les captures d'accès refusés
DENIED_ACCESS_FOLDER = r"C:\Users\OSIRIS\Pictures\images"

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
        self.head_turn_detected = False
        self.antispoofing_passed = False
        self.antispoofing_start_time = None
        self.current_face_location = None

        # Créer le dossier pour les captures si nécessaire
        if not os.path.exists(DENIED_ACCESS_FOLDER):
            os.makedirs(DENIED_ACCESS_FOLDER)
            logger.log_info(f"Dossier créé: {DENIED_ACCESS_FOLDER}")

        # Variable pour stocker la dernière frame capturée
        self.last_frame = None

        logger.log_info("Fenêtre utilisateur initialisée")

        # Afficher directement la page d'accueil utilisateur
        self.setup_user_home_page()

    def capture_denied_access_image(self, frame=None):
        """
        Capturer et sauvegarder l'image lors d'un accès refusé
        
        Args:
            frame: Frame à sauvegarder (utilise self.last_frame si None)
            
        Returns:
            str: Chemin du fichier sauvegardé ou None si échec
        """
        try:
            # Utiliser la frame fournie ou la dernière frame capturée
            img_frame = frame if frame is not None else self.last_frame
            
            if img_frame is None:
                logger.log_warning("Pas de frame disponible pour la capture")
                return None
            
            # Générer un nom de fichier unique avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"denied_{timestamp}.jpg"
            filepath = os.path.join(DENIED_ACCESS_FOLDER, filename)
            
            # Sauvegarder l'image
            cv2.imwrite(filepath, img_frame)
            logger.log_info(f"Image capturée: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.log_error(f"Erreur capture image: {e}")
            return None

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

        # Réinitialiser les variables
        self.is_paused = False
        self.face_not_recognized_count = 0
        self.reset_antispoofing()

        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame gauche (caméra)
        left_frame = tk.Frame(main_frame, bg='black')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame droite (statuts) - LARGEUR FIXE
        right_frame = tk.Frame(main_frame, bg='white', width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        right_frame.pack_propagate(False)  # Empêcher le redimensionnement

        # Barre d'outils en haut de la caméra
        toolbar = tk.Frame(left_frame, bg='#2C3E50', height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # Bouton retour
        back_button = tk.Button(
            toolbar,
            text="← Retour",
            font=('Arial', 11, 'bold'),
            command=self.return_to_user_home,
            bg='#E74C3C',
            fg='white',
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        back_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Titre de la page
        title = tk.Label(
            toolbar,
            text="🎥 Reconnaissance en cours...",
            font=('Arial', 14, 'bold'),
            bg='#2C3E50',
            fg='white'
        )
        title.pack(side=tk.LEFT, padx=20)

        # IMPORTANT: Créer le StatusPanel AVANT le CameraWidget
        self.status_panel = StatusPanel(right_frame)

        # Forcer la mise à jour de l'interface pour que les widgets soient créés
        self.root.update_idletasks()

        # Créer le CameraWidget APRÈS
        self.camera_widget = CameraWidget(left_frame, self.process_callback)

        # Démarrer la caméra
        camera_started = self.camera_widget.start()

        if not camera_started:
            messagebox.showerror(
                "Erreur Caméra",
                "Impossible de démarrer la caméra!\n\n"
                "Vérifiez que:\n"
                "- Une webcam est connectée\n"
                "- Aucune autre application n'utilise la caméra\n"
                "- Les pilotes de la caméra sont installés"
            )
            self.return_to_user_home()
            return

        logger.log_info("Page de reconnaissance affichée - Caméra démarrée")

    def process_callback(self, frame):
        """Callback principal - VERSION OPTIMISÉE"""
        try:
            if not hasattr(self, 'face_engine') or not self.face_engine:
                cv2.putText(frame, "ERREUR: Moteur non initialise", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                return frame

            if not hasattr(self, 'status_panel') or not self.status_panel:
                cv2.putText(frame, "ERREUR: Panel non initialise", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                return frame

            return self.process_frame(frame)

        except Exception as e:
            logger.log_error(f"❌ ERREUR CALLBACK: {e}")
            cv2.putText(frame, f"ERREUR: {str(e)[:50]}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            return frame

    def process_frame_safe(self, frame):
        """Version safe de process_frame (ne plante JAMAIS)"""
        try:
            if self.is_paused:
                return frame

            # Détection safe
            face_locations, face_encodings = self.face_engine.detect_faces(frame)

            if len(face_locations) == 0:
                cv2.putText(frame, "⏳ Pas de visage", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                if hasattr(self, 'status_panel'):
                    self.status_panel.update_status("⏳ En attente d'un visage...", "info")
                return frame

            # Premier visage
            top, right, bottom, left = face_locations[0]
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 0), 2)
            cv2.putText(frame, "VISAGE DETECTE !", (left, bottom + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Anti-spoofing simple (DÉSACTIVÉ)
            # if not self.antispoofing_passed:
            #     cv2.putText(frame, "🛡️ Anti-spoofing...", (20, 110),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Reconnaissance simple
            personne_id, username, _, similarity = self.face_engine.recognize_face(face_encodings[0])
            if personne_id:
                cv2.putText(frame, f"✅ {username}", (left, bottom + 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "❌ Inconnu", (left, bottom + 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            return frame

        except Exception as e:
            logger.log_error(f"process_frame_safe crash: {e}")
            cv2.putText(frame, "ERREUR DETECTION", (20, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return frame

    def process_frame(self, frame):
        """
        Traiter frame - TOLÉRANCE MAXIMALE pour rotation rapide
        """
        try:
            if self.is_paused:
                cv2.putText(frame, "PAUSE", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 2)
                return frame

            # Détection visages
            face_locations, face_encodings = self.face_engine.detect_faces(frame)

            # === PAS DE VISAGE DÉTECTÉ ===
            if len(face_locations) == 0:
                # ⚡ TOLÉRANCE MAXIMALE pendant anti-spoofing
                if self.antispoofing_active:
                    if not hasattr(self, 'face_lost_frames'):
                        self.face_lost_frames = 0

                    self.face_lost_frames += 1

                    # Afficher message positif
                    height, width = frame.shape[:2]

                    # Rectangle info semi-transparent
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (10, 40), (width - 10, 160), (50, 50, 50), -1)
                    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

                    cv2.putText(frame, "Continuez le mouvement...", (25, 75),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                    cv2.putText(frame, "Tournez votre tete GAUCHE et DROITE", (25, 110),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
                    cv2.putText(frame, f"Detection: {self.face_lost_frames}/{self.max_lost_frames}", (25, 145),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)

                    # Afficher progrès
                    stats = self.antispoof_detector.get_detection_stats()
                    progress_y = 200

                    if stats['left_movement']:
                        cv2.putText(frame, "✅ GAUCHE valide", (30, progress_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "⏳ Tournez a GAUCHE", (30, progress_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

                    if stats['right_movement']:
                        cv2.putText(frame, "✅ DROITE valide", (30, progress_y + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "⏳ Tournez a DROITE", (30, progress_y + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

                    # Barre de progression
                    progress = (self.face_lost_frames / self.max_lost_frames) * 100
                    bar_width = int((width - 60) * (progress / 100))
                    bar_y = height - 50

                    # Fond barre
                    cv2.rectangle(frame, (30, bar_y), (width - 30, bar_y + 20), (80, 80, 80), -1)
                    # Barre progression
                    color = (0, 165, 255) if progress < 70 else (0, 100, 255)
                    cv2.rectangle(frame, (30, bar_y), (30 + bar_width, bar_y + 20), color, -1)
                    # Contour
                    cv2.rectangle(frame, (30, bar_y), (width - 30, bar_y + 20), (200, 200, 200), 2)

                    # Si trop longtemps perdu
                    if self.face_lost_frames > self.max_lost_frames:
                        logger.log_warning(f"⚠️ Visage perdu > {self.max_lost_frames} frames")

                        # Message d'avertissement
                        cv2.rectangle(frame, (20, height // 2 - 60), (width - 20, height // 2 + 60), (0, 0, 200), -1)
                        cv2.rectangle(frame, (20, height // 2 - 60), (width - 20, height // 2 + 60), (0, 0, 255), 4)
                        cv2.putText(frame, "REPOSITIONNEZ-VOUS", (width // 2 - 220, height // 2 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                        cv2.putText(frame, "Face a la camera", (width // 2 - 150, height // 2 + 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                        # Reset après message
                        if self.face_lost_frames > self.max_lost_frames + 15:
                            self.reset_antispoofing()

                    return frame

                # Pas en anti-spoofing
                cv2.putText(frame, "Aucun visage detecte", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(frame, "Positionnez-vous face a la camera", (20, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                if hasattr(self, 'status_panel') and self.status_panel:
                    self.status_panel.update_status("⏳ En attente...", "info")

                return frame

            # ⚡ Visage détecté - reset compteur
            self.face_lost_frames = 0
            self.last_known_face_location = face_locations[0]

            # Un visage détecté
            face_location = face_locations[0]
            face_encoding = face_encodings[0] if len(face_encodings) > 0 else None
            top, right, bottom, left = face_location

            if face_encoding is None:
                cv2.putText(frame, "Erreur encodage", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                return frame

            # === PHASE 1: ANTI-SPOOFING (DÉSACTIVÉ) ===
            # if not self.antispoofing_passed:
            #     return self.process_antispoofing(frame, face_location, face_encoding)

            # === PHASE 2: RECONNAISSANCE (directe) ===
            personne_id, username, password, similarity = self.face_engine.recognize_face(face_encoding)

            if personne_id:
                self.face_not_recognized_count = 0
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)
                cv2.putText(frame, f"RECONNU: {username}", (left, bottom + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f"Score: {similarity * 100:.1f}%", (left, bottom + 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                if hasattr(self, 'status_panel') and self.status_panel:
                    self.status_panel.update_status(f"✅ Reconnu: {username}", "success")
                    self.status_panel.update_similarity(similarity)

                self.is_paused = True
                self.root.after(500, lambda: self.grant_access_direct(personne_id, username, similarity))

            else:
                self.face_not_recognized_count += 1
                # Stocker la frame pour capture potentielle
                self.last_frame = frame.copy()
                
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 165, 255), 3)
                cv2.putText(frame, f"INCONNU", (left, bottom + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.putText(frame, f"Tentative {self.face_not_recognized_count}/3", (left, bottom + 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

                if hasattr(self, 'status_panel') and self.status_panel:
                    self.status_panel.update_status(
                        f"❌ Non reconnu ({self.face_not_recognized_count}/3)",
                        "warning"
                    )

                if self.face_not_recognized_count >= 3:
                    self.is_paused = True
                    # Signal Arduino - LED rouge + buzzer
                    signal_access_denied()
                    # Capturer l'image de l'intrus et enregistrer l'accès refusé
                    image_path = self.capture_denied_access_image()
                    self.access_service.log_access_attempt(None, 'DENIED', 'FACE_ONLY', image_url=image_path)
                    logger.log_warning(f"Accès refusé - Visage non reconnu 3x - Image: {image_path}")
                    # Envoyer email d'alerte (dans un thread pour ne pas bloquer)
                    threading.Thread(target=send_security_alert, args=(image_path, "Visage non reconnu (3 tentatives)"), daemon=True).start()
                    self.root.after(500, lambda: self.request_pin_after_failures())

            return frame

        except Exception as e:
            logger.log_error(f"❌ Erreur: {e}")
            import traceback
            logger.log_error(traceback.format_exc())
            cv2.putText(frame, "ERREUR", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return frame

    """Fonctions anti-spoofing SIMPLIFIÉES pour main_window.py"""

    def process_antispoofing(self, frame, face_location, face_encoding):
        """Anti-spoofing RAPIDE - Instructions claires gauche/droite"""
        top, right, bottom, left = face_location
        height, width = frame.shape[:2]

        # Initialiser
        if not self.antispoofing_active:
            self.antispoofing_active = True
            self.antispoofing_start_time = datetime.now()
            self.head_turn_detected = False
            self.face_lost_frames = 0
            logger.log_info("🛡️ Démarrage anti-spoofing")

        # Rectangle autour du visage (cyan)
        cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 0), 3)

        # Obtenir les stats
        stats = self.antispoof_detector.get_detection_stats()
        left_ok = stats['left_movement']
        right_ok = stats['right_movement']

        # === BARRE D'INSTRUCTION EN HAUT ===
        cv2.rectangle(frame, (0, 0), (width, 80), (40, 40, 40), -1)
        
        # Message d'instruction dynamique
        if left_ok and right_ok:
            instruction = "PARFAIT ! Verification en cours..."
            color = (0, 255, 0)
        elif left_ok:
            instruction = "Maintenant tournez la tete a DROITE -->"
            color = (0, 255, 255)
        elif right_ok:
            instruction = "<-- Maintenant tournez la tete a GAUCHE"
            color = (0, 255, 255)
        else:
            instruction = "Tournez la tete a GAUCHE <-- puis a DROITE -->"
            color = (255, 255, 255)

        cv2.putText(frame, instruction, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # === INDICATEURS VISUELS SUR LES CÔTÉS ===
        indicator_y = height // 2

        # Indicateur GAUCHE
        if left_ok:
            cv2.circle(frame, (50, indicator_y), 30, (0, 255, 0), -1)
            cv2.putText(frame, "OK", (35, indicator_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            cv2.circle(frame, (50, indicator_y), 30, (0, 255, 255), 3)
            cv2.arrowedLine(frame, (100, indicator_y), (60, indicator_y), (0, 255, 255), 4, tipLength=0.4)

        # Indicateur DROITE
        if right_ok:
            cv2.circle(frame, (width - 50, indicator_y), 30, (0, 255, 0), -1)
            cv2.putText(frame, "OK", (width - 65, indicator_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            cv2.circle(frame, (width - 50, indicator_y), 30, (0, 255, 255), 3)
            cv2.arrowedLine(frame, (width - 100, indicator_y), (width - 60, indicator_y), (0, 255, 255), 4, tipLength=0.4)

        # === TIMER (15 secondes max) ===
        elapsed = (datetime.now() - self.antispoofing_start_time).total_seconds()
        remaining = max(0, 15 - int(elapsed))
        
        timer_color = (0, 255, 0) if remaining > 5 else (0, 165, 255) if remaining > 3 else (0, 0, 255)
        cv2.putText(frame, f"{remaining}s", (width - 60, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, timer_color, 2)

        # === DÉTECTION ===
        if not self.head_turn_detected:
            head_turn = self.antispoof_detector.detect_head_turn(frame, face_location)

            if head_turn:
                self.head_turn_detected = True
                logger.log_info("✅ Anti-spoofing validé!")

                # Bannière de succès
                cv2.rectangle(frame, (0, height // 2 - 40), (width, height // 2 + 40), (0, 180, 0), -1)
                cv2.putText(frame, "VERIFICATION REUSSIE !", (width // 2 - 180, height // 2 + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

                # Passer à la reconnaissance après 500ms
                self.root.after(500, self.complete_antispoofing)

        # Mise à jour du status panel
        if hasattr(self, 'status_panel') and self.status_panel:
            if self.head_turn_detected:
                self.status_panel.update_status("✅ Vérifié !", "success")
            else:
                progress = f"{'✅' if left_ok else '⬜'} Gauche | {'✅' if right_ok else '⬜'} Droite"
                self.status_panel.update_status(f"🛡️ {progress}", "info")

        # Timeout (15 secondes au lieu de 30)
        if elapsed > 15:
            self.fail_antispoofing()

        return frame

    def next_antispoofing_step(self):
        """Passer à l'étape suivante"""
        self.antispoofing_step = 2
        logger.log_info("Passage à l'étape 2: Mouvement de tête")

    def complete_antispoofing(self):
        """Validation"""
        texture_score = 0.8
        liveness_score = self.antispoof_detector.calculate_liveness_score(
            True, self.head_turn_detected, texture_score
        )

        if self.antispoof_detector.is_live(liveness_score):
            self.antispoofing_passed = True
            self.antispoofing_active = False
            self.status_panel.update_status(f"✅ Validé ({liveness_score * 100:.0f}%)", "success")
            messagebox.showinfo("✅ Réussi", f"Score: {liveness_score * 100:.0f}%\n\nReconnaissance...")
        else:
            self.fail_antispoofing()

    def fail_antispoofing(self):
        """Échec"""
        self.status_panel.update_status("❌ Échec", "error")
        # Capturer l'image de l'intrus
        image_path = self.capture_denied_access_image()
        # Signal Arduino - LED rouge + buzzer
        signal_access_denied()
        self.access_service.log_access_attempt(None, 'DENIED', 'FACE_ONLY', image_url=image_path, similarity_score=0.0)
        logger.log_warning(f"Échec antispoofing - Image: {image_path}")
        # Envoyer email d'alerte
        threading.Thread(target=send_security_alert, args=(image_path, "Échec anti-spoofing"), daemon=True).start()
        messagebox.showerror("❌ Échec", "Échec vérification.\nRéessayez.")
        self.reset_antispoofing()
        self.is_paused = False

    def reset_antispoofing(self):
        """Reset"""
        self.antispoofing_active = False
        self.antispoofing_passed = False
        self.head_turn_detected = False
        self.antispoofing_start_time = None
        self.face_lost_frames = 0
        if hasattr(self, 'antispoof_detector'):
            self.antispoof_detector.reset_counters()

    def grant_access_direct(self, personne_id, username, similarity):
        """Accorder l'accès directement"""
        self.status_panel.update_status(f"✅ ACCÈS AUTORISÉ: {username}", "success")

        # Signal Arduino - LED verte + buzzer
        signal_access_granted()

        self.access_service.log_access_attempt(
            personne_id, 'GRANTED', 'FACE_ONLY',
            similarity_score=similarity
        )

        self.access_service.log_antispoofing(
            personne_id,
            blink_detected=False,
            headturn_detected=self.head_turn_detected if hasattr(self, 'head_turn_detected') else False,
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

                    # Signal Arduino - LED verte + buzzer
                    signal_access_granted()

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
                # Signal Arduino - LED rouge + buzzer
                signal_access_denied()
                # Capturer l'image de l'intrus
                image_path = self.capture_denied_access_image()
                self.access_service.log_access_attempt(None, 'DENIED', 'PIN_ONLY', image_url=image_path)
                logger.log_warning(f"Échec d'authentification par PIN - Image: {image_path}")
                # Envoyer email d'alerte
                threading.Thread(target=send_security_alert, args=(image_path, "PIN/Mot de passe incorrect"), daemon=True).start()
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