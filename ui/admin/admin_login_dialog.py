# admin_login_dialog.py
# No major changes needed, as it already handles login check in DB.

import tkinter as tk
from tkinter import messagebox
from typing import Optional
from utils.logger import Logger

logger = Logger()


class AdminLoginDialog:
    """Dialogue pour l'authentification administrateur"""

    def __init__(self, parent, auth_manager, user_service):
        """
        Initialiser le dialogue de login admin
        Args:
            parent: Fenêtre parent
            auth_manager: Gestionnaire d'authentification
            user_service: Service utilisateur
        """
        self.result = None
        self.auth_manager = auth_manager
        self.user_service = user_service

        # Créer la fenêtre modale
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔐 Connexion Administrateur")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg='#2C3E50')

        # Centrer la fenêtre
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()

    def setup_ui(self):
        """Configurer l'interface"""
        # Frame principal avec gradient simulé
        main_frame = tk.Frame(self.dialog, bg='#2C3E50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Icône/Logo
        logo_frame = tk.Frame(main_frame, bg='#2C3E50')
        logo_frame.pack(pady=20)
        logo_label = tk.Label(
            logo_frame,
            text="🔒",
            font=('Arial', 60),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        logo_label.pack()

        # Titre
        title = tk.Label(
            main_frame,
            text="ESPACE ADMINISTRATEUR",
            font=('Arial', 18, 'bold'),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        title.pack(pady=5)

        subtitle = tk.Label(
            main_frame,
            text="Accès réservé aux administrateurs",
            font=('Arial', 10),
            bg='#2C3E50',
            fg='#95A5A6'
        )
        subtitle.pack(pady=5)

        # Frame du formulaire
        form_frame = tk.Frame(main_frame, bg='#34495E', relief=tk.RAISED, bd=2)
        form_frame.pack(pady=20, fill=tk.X)

        # Padding interne
        inner_frame = tk.Frame(form_frame, bg='#34495E')
        inner_frame.pack(padx=20, pady=20)

        # Nom d'utilisateur
        username_label = tk.Label(
            inner_frame,
            text="👤 Nom d'utilisateur",
            font=('Arial', 11, 'bold'),
            bg='#34495E',
            fg='#ECF0F1'
        )
        username_label.pack(anchor='w', pady=(0, 5))
        self.username_entry = tk.Entry(
            inner_frame,
            font=('Arial', 12),
            width=30,
            relief=tk.FLAT,
            bd=2
        )
        self.username_entry.pack(pady=(0, 15), ipady=5)
        self.username_entry.focus()

        # Mot de passe
        password_label = tk.Label(
            inner_frame,
            text="🔑 Mot de passe",
            font=('Arial', 11, 'bold'),
            bg='#34495E',
            fg='#ECF0F1'
        )
        password_label.pack(anchor='w', pady=(0, 5))
        self.password_entry = tk.Entry(
            inner_frame,
            font=('Arial', 12),
            width=30,
            show='●',
            relief=tk.FLAT,
            bd=2
        )
        self.password_entry.pack(ipady=5)

        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.login())

        # Boutons
        button_frame = tk.Frame(main_frame, bg='#2C3E50')
        button_frame.pack(pady=20)

        login_btn = tk.Button(
            button_frame,
            text="🔓 SE CONNECTER",
            font=('Arial', 11, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.login
        )
        login_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="✗ Annuler",
            font=('Arial', 11, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.cancel
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Message d'avertissement
        warning = tk.Label(
            main_frame,
            text="⚠️ Accès non autorisé sera enregistré",
            font=('Arial', 9, 'italic'),
            bg='#2C3E50',
            fg='#E74C3C'
        )
        warning.pack()

    def login(self):
        """Tenter la connexion"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires!")
            return

        # Récupérer l'utilisateur
        user = self.user_service.get_user_by_username(username)
        if not user:
            logger.log_warning(f"Tentative de connexion admin échouée: utilisateur '{username}' introuvable")
            messagebox.showerror("Erreur", "Identifiants incorrects!")
            return

        # Vérifier le rôle ADMIN
        if user.role != 'ADMIN':
            logger.log_warning(f"Tentative d'accès admin par utilisateur non-admin: {username}")
            messagebox.showerror("Accès Refusé", "Vous n'avez pas les droits administrateur!")
            return

        # Vérifier le mot de passe
        if not self.auth_manager.verify_password(password, user.password):
            logger.log_warning(f"Mot de passe incorrect pour admin: {username}")
            messagebox.showerror("Erreur", "Identifiants incorrects!")
            return

        # Vérifier si actif
        if not user.is_active:
            logger.log_warning(f"Tentative de connexion par admin désactivé: {username}")
            messagebox.showerror("Accès Refusé", "Ce compte est désactivé!")
            return

        # Connexion réussie
        logger.log_info(f"✓ Connexion admin réussie: {username}")
        self.result = user
        self.dialog.destroy()

    def cancel(self):
        """Annuler"""
        self.result = None
        self.dialog.destroy()

    def get_admin_user(self):
        """Obtenir l'utilisateur admin connecté"""
        self.dialog.wait_window()
        return self.result
