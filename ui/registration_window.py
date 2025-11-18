# ui/registration_window.py

"""
Fenêtre d'enregistrement d'un nouvel utilisateur
Permet de capturer la photo faciale et les informations de l'utilisateur
"""

import tkinter as tk
from tkinter import messagebox, ttk
import cv2
from PIL import Image, ImageTk
from datetime import datetime
from typing import Optional

from utils.logger import Logger

logger = Logger()


class RegistrationWindow:
    """
    Fenêtre d'enregistrement d'un nouvel utilisateur
    """

    def __init__(self, parent, face_engine, user_service, profile_service):
        """
        Initialiser la fenêtre d'enregistrement

        Args:
            parent: Fenêtre parent
            face_engine: Moteur de reconnaissance faciale
            user_service: Service utilisateur
            profile_service: Service profil facial
        """
        self.face_engine = face_engine
        self.user_service = user_service
        self.profile_service = profile_service

        self.camera = None
        self.camera_running = False
        self.captured_frame = None

        # Créer la fenêtre
        self.window = tk.Toplevel(parent)
        self.window.title("📝 Enregistrement Utilisateur - Smart Home Access")
        self.window.geometry("1100x750")
        self.window.resizable(False, False)
        self.window.configure(bg='#ECF0F1')

        # Centrer
        self.window.transient(parent)
        self.window.grab_set()

        logger.log_info("Fenêtre d'enregistrement ouverte")

        self.setup_ui()

    def setup_ui(self):
        """Configurer l'interface"""
        # Container principal
        main_container = tk.Frame(self.window, bg='#ECF0F1')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ====================================================================
        # PARTIE GAUCHE - CAPTURE PHOTO
        # ====================================================================
        left_frame = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Titre
        title_label = tk.Label(
            left_frame,
            text="📷 Capture Faciale",
            font=('Arial', 16, 'bold'),
            bg='#3498DB',
            fg='white',
            pady=10
        )
        title_label.pack(fill=tk.X)

        # Zone vidéo
        video_frame = tk.Frame(left_frame, bg='#2C3E50', relief=tk.SUNKEN, bd=3)
        video_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(
            video_frame,
            text="📹 Caméra non activée\n\nCliquez sur 'Démarrer Caméra'",
            font=('Arial', 14),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Boutons caméra
        camera_buttons_frame = tk.Frame(left_frame, bg='white')
        camera_buttons_frame.pack(pady=10)

        self.start_camera_btn = tk.Button(
            camera_buttons_frame,
            text="▶️ Démarrer Caméra",
            font=('Arial', 11, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=15,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.start_camera
        )
        self.start_camera_btn.pack(side=tk.LEFT, padx=5)

        self.capture_btn = tk.Button(
            camera_buttons_frame,
            text="📸 Capturer",
            font=('Arial', 11, 'bold'),
            bg='#3498DB',
            fg='white',
            padx=15,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED,
            command=self.capture_photo
        )
        self.capture_btn.pack(side=tk.LEFT, padx=5)

        self.stop_camera_btn = tk.Button(
            camera_buttons_frame,
            text="⏹️ Arrêter",
            font=('Arial', 11, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=15,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED,
            command=self.stop_camera
        )
        self.stop_camera_btn.pack(side=tk.LEFT, padx=5)

        # Statut
        self.capture_status_label = tk.Label(
            left_frame,
            text="ℹ️ Cliquez sur 'Démarrer Caméra' pour commencer",
            font=('Arial', 10, 'italic'),
            bg='white',
            fg='#7F8C8D'
        )
        self.capture_status_label.pack(pady=10)

        # ====================================================================
        # PARTIE DROITE - FORMULAIRE
        # ====================================================================
        right_frame = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Titre
        form_title = tk.Label(
            right_frame,
            text="📋 Informations Utilisateur",
            font=('Arial', 16, 'bold'),
            bg='#9B59B6',
            fg='white',
            pady=10
        )
        form_title.pack(fill=tk.X)

        # Scrollable frame pour le formulaire
        canvas = tk.Canvas(right_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        scrollbar.pack(side="right", fill="y")

        # ===== FORMULAIRE =====
        form_frame = tk.Frame(scrollable_frame, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Nom d'utilisateur
        self.create_form_field(form_frame, "👤 Nom d'utilisateur *", 0)
        self.username_entry = tk.Entry(form_frame, font=('Arial', 11), width=30)
        self.username_entry.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 15))

        # Email
        self.create_form_field(form_frame, "📧 Email *", 2)
        self.email_entry = tk.Entry(form_frame, font=('Arial', 11), width=30)
        self.email_entry.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 15))

        # Téléphone
        self.create_form_field(form_frame, "📱 Téléphone", 4)
        self.phone_entry = tk.Entry(form_frame, font=('Arial', 11), width=30)
        self.phone_entry.grid(row=5, column=0, sticky='ew', padx=10, pady=(0, 15))

        # Rôle
        self.create_form_field(form_frame, "🎭 Rôle *", 6)
        self.role_var = tk.StringVar(value="USER")
        role_frame = tk.Frame(form_frame, bg='white')
        role_frame.grid(row=7, column=0, sticky='ew', padx=10, pady=(0, 15))

        roles = [("👤 Utilisateur", "USER"), ("👑 Admin", "ADMIN"), ("👥 Invité", "GUEST")]
        for text, value in roles:
            tk.Radiobutton(
                role_frame,
                text=text,
                variable=self.role_var,
                value=value,
                font=('Arial', 10),
                bg='white',
                activebackground='white'
            ).pack(side=tk.LEFT, padx=10)

        # Mot de passe
        self.create_form_field(form_frame, "🔒 Mot de passe (PIN) *", 8)
        self.password_entry = tk.Entry(form_frame, font=('Arial', 11), width=30, show='●')
        self.password_entry.grid(row=9, column=0, sticky='ew', padx=10, pady=(0, 15))

        # Confirmation mot de passe
        self.create_form_field(form_frame, "🔒 Confirmer mot de passe *", 10)
        self.password_confirm_entry = tk.Entry(form_frame, font=('Arial', 11), width=30, show='●')
        self.password_confirm_entry.grid(row=11, column=0, sticky='ew', padx=10, pady=(0, 15))

        # Type d'accès
        self.create_form_field(form_frame, "🚪 Type d'accès", 12)
        self.access_type_var = tk.StringVar(value="Permanent")
        access_frame = tk.Frame(form_frame, bg='white')
        access_frame.grid(row=13, column=0, sticky='ew', padx=10, pady=(0, 15))

        tk.Radiobutton(
            access_frame,
            text="♾️ Permanent",
            variable=self.access_type_var,
            value="Permanent",
            font=('Arial', 10),
            bg='white',
            command=self.toggle_temporary_fields
        ).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(
            access_frame,
            text="⏰ Temporaire",
            variable=self.access_type_var,
            value="Temporaire",
            font=('Arial', 10),
            bg='white',
            command=self.toggle_temporary_fields
        ).pack(side=tk.LEFT, padx=10)

        # Champs temporaires (cachés par défaut)
        self.temp_frame = tk.Frame(form_frame, bg='#F8F9FA', relief=tk.GROOVE, bd=2)
        self.temp_frame.grid(row=14, column=0, sticky='ew', padx=10, pady=(0, 15))
        self.temp_frame.grid_remove()  # Caché au départ

        tk.Label(
            self.temp_frame,
            text="📅 Date de début",
            font=('Arial', 10, 'bold'),
            bg='#F8F9FA'
        ).grid(row=0, column=0, sticky='w', padx=10, pady=(10, 5))

        self.start_date_entry = tk.Entry(self.temp_frame, font=('Arial', 10), width=20)
        self.start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.start_date_entry.grid(row=1, column=0, padx=10, pady=(0, 10))

        tk.Label(
            self.temp_frame,
            text="📅 Date de fin",
            font=('Arial', 10, 'bold'),
            bg='#F8F9FA'
        ).grid(row=2, column=0, sticky='w', padx=10, pady=(5, 5))

        self.end_date_entry = tk.Entry(self.temp_frame, font=('Arial', 10), width=20)
        self.end_date_entry.insert(0, (datetime.now()).strftime("%Y-%m-%d 23:59"))
        self.end_date_entry.grid(row=3, column=0, padx=10, pady=(0, 10))

        # Notes
        self.create_form_field(form_frame, "📝 Notes (optionnel)", 15)
        self.notes_text = tk.Text(form_frame, font=('Arial', 10), width=30, height=4)
        self.notes_text.grid(row=16, column=0, sticky='ew', padx=10, pady=(0, 15))

        # Boutons d'action
        action_frame = tk.Frame(form_frame, bg='white')
        action_frame.grid(row=17, column=0, pady=20)

        self.save_btn = tk.Button(
            action_frame,
            text="💾 ENREGISTRER",
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=30,
            pady=12,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.save_user
        )
        self.save_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = tk.Button(
            action_frame,
            text="❌ Annuler",
            font=('Arial', 12, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=30,
            pady=12,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.window.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def create_form_field(self, parent, label_text, row):
        """Créer un champ de formulaire avec label"""
        label = tk.Label(
            parent,
            text=label_text,
            font=('Arial', 11, 'bold'),
            bg='white',
            fg='#2C3E50',
            anchor='w'
        )
        label.grid(row=row, column=0, sticky='w', padx=10, pady=(10, 5))

    def toggle_temporary_fields(self):
        """Afficher/cacher les champs d'accès temporaire"""
        if self.access_type_var.get() == "Temporaire":
            self.temp_frame.grid()
        else:
            self.temp_frame.grid_remove()

    # ========================================================================
    # GESTION CAMÉRA
    # ========================================================================

    def start_camera(self):
        """Démarrer la caméra"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Erreur", "Impossible d'ouvrir la caméra!")
                return

            self.camera_running = True

            self.start_camera_btn.config(state=tk.DISABLED)
            self.capture_btn.config(state=tk.NORMAL)
            self.stop_camera_btn.config(state=tk.NORMAL)

            self.capture_status_label.config(
                text="✅ Caméra active - Positionnez votre visage",
                fg='#27AE60'
            )

            self.update_frame()
            logger.log_info("Caméra démarrée")

        except Exception as e:
            logger.log_error(f"Erreur démarrage caméra: {e}")
            messagebox.showerror("Erreur", f"Erreur: {e}")

    def update_frame(self):
        """Mettre à jour l'affichage vidéo"""
        if self.camera_running and self.camera:
            ret, frame = self.camera.read()
            if ret:
                # Convertir BGR -> RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Redimensionner
                frame_rgb = cv2.resize(frame_rgb, (480, 360))

                # Convertir en ImageTk
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)

                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

            # Répéter
            self.window.after(30, self.update_frame)

    def capture_photo(self):
        """Capturer une photo"""
        if not self.camera or not self.camera.isOpened():
            messagebox.showwarning("Attention", "Caméra non démarrée!")
            return

        ret, frame = self.camera.read()
        if ret:
            self.captured_frame = frame.copy()
            self.capture_status_label.config(
                text="✅ Photo capturée avec succès !",
                fg='#27AE60'
            )
            logger.log_info("Photo capturée")

            # Arrêter la caméra
            self.stop_camera()
        else:
            messagebox.showerror("Erreur", "Échec de la capture!")

    def stop_camera(self):
        """Arrêter la caméra"""
        self.camera_running = False

        if self.camera:
            self.camera.release()
            self.camera = None

        self.start_camera_btn.config(state=tk.NORMAL)
        self.capture_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.DISABLED)

        if self.captured_frame is None:
            self.video_label.config(
                text="📹 Caméra arrêtée",
                image=''
            )

        logger.log_info("Caméra arrêtée")

    # ========================================================================
    # SAUVEGARDE
    # ========================================================================

    def save_user(self):
        """Enregistrer l'utilisateur"""
        # Validation
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        password_confirm = self.password_confirm_entry.get().strip()

        if not username or not email or not password:
            messagebox.showerror("Erreur", "Les champs obligatoires (*) doivent être remplis!")
            return

        if password != password_confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas!")
            return

        if self.captured_frame is None:
            messagebox.showerror("Erreur", "Aucune photo capturée!")
            return

        try:
            # Créer l'utilisateur
            user_data = {
                "username": username,
                "email": email,
                "phone": self.phone_entry.get().strip(),
                "role": self.role_var.get(),
                "password": password,
                "is_active": True
            }

            # Ajouter dans la base
            user_id = self.user_service.create_user(**user_data)

            if user_id:
                # Extraire l'embedding facial
                embedding = self.face_engine.extract_embedding(self.captured_frame)

                if embedding is not None:
                    # Sauvegarder le profil facial
                    self.profile_service.save_profile(user_id, embedding)

                    logger.log_info(f"✓ Utilisateur {username} enregistré avec succès (ID: {user_id})")
                    messagebox.showinfo(
                        "Succès",
                        f"✅ Utilisateur '{username}' enregistré avec succès !\n\n"
                        f"ID: {user_id}\n"
                        f"Profil facial: ✓ Enregistré"
                    )

                    self.window.destroy()
                else:
                    messagebox.showerror(
                        "Erreur",
                        "Impossible d'extraire l'embedding facial!\n"
                        "Utilisateur créé mais sans profil facial."
                    )
            else:
                messagebox.showerror("Erreur", "Échec de la création de l'utilisateur!")

        except Exception as e:
            logger.log_error(f"Erreur enregistrement utilisateur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement: {e}")

    def __del__(self):
        """Nettoyage à la destruction"""
        if self.camera:
            self.camera.release()


# Test
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    # Mock des services
    class MockFaceEngine:
        def extract_embedding(self, frame):
            return [0.1] * 128

    class MockUserService:
        def create_user(self, **kwargs):
            return 1

    class MockProfileService:
        def save_profile(self, user_id, embedding):
            return True

    window = RegistrationWindow(
        root,
        MockFaceEngine(),
        MockUserService(),
        MockProfileService()
    )

    root.mainloop()