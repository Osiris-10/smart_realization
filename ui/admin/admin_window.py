# admin_window.py
# Mode administrateur avec navigation propre et retour au menu principal

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import numpy as np
from typing import Optional
from datetime import datetime
from database.connection import DatabaseConnection
from core.face_recognition import FaceRecognitionEngine
from services.user_service import UserService
from services.profile_service import ProfileService
from services.access_service import AccessService
from utils.logger import Logger
from utils.encryption import EncryptionManager
import json

try:
    import face_recognition
except ImportError:
    print("Install face_recognition: pip install face_recognition")

logger = Logger()


class AdminWindow:
    """Fenêtre d'administration avec connexion et retour au menu"""

    def __init__(self, db, face_engine, user_service, profile_service, access_service, return_callback=None):
        # Services
        self.db = db
        self.user_service = user_service
        self.profile_service = profile_service
        self.access_service = access_service
        self.face_engine = face_engine
        self.encryption = EncryptionManager()
        self.return_callback = return_callback  # Callback pour retour au menu principal

        # Créer la fenêtre
        self.root = tk.Tk()
        self.root.title("Panel Administrateur - Reconnaissance Faciale")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f5f5f5')

        self.admin_user = None

        # Afficher le formulaire de connexion d'abord
        self.show_login_form()

        # Gestionnaire de fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.mainloop()

    def show_login_form(self):
        """Afficher le formulaire de connexion admin"""
        # Nettoyer la fenêtre
        if hasattr(self, 'main_frame'):
            try:
                self.main_frame.pack_forget()
            except:
                pass

        self.login_frame = tk.Frame(self.root, bg='#2C3E50')
        self.login_frame.pack(expand=True, fill='both')

        # Container centré
        login_container = tk.Frame(self.login_frame, bg='#34495E', padx=40, pady=40)
        login_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Titre
        tk.Label(
            login_container,
            text="🔐 CONNEXION ADMINISTRATEUR",
            font=('Arial', 24, 'bold'),
            bg='#34495E',
            fg='white'
        ).pack(pady=(0, 30))

        # Formulaire
        form_frame = tk.Frame(login_container, bg='#34495E')
        form_frame.pack(pady=20)

        # Username
        tk.Label(
            form_frame,
            text="Nom d'utilisateur:",
            font=('Arial', 12),
            bg='#34495E',
            fg='#ECF0F1'
        ).grid(row=0, column=0, sticky=tk.W, pady=10, padx=(0, 10))

        self.user_entry = tk.Entry(form_frame, font=('Arial', 12), width=30)
        self.user_entry.grid(row=0, column=1, pady=10)
        self.user_entry.focus()

        # Password
        tk.Label(
            form_frame,
            text="Mot de passe:",
            font=('Arial', 12),
            bg='#34495E',
            fg='#ECF0F1'
        ).grid(row=1, column=0, sticky=tk.W, pady=10, padx=(0, 10))

        self.pw_entry = tk.Entry(form_frame, show="*", font=('Arial', 12), width=30)
        self.pw_entry.grid(row=1, column=1, pady=10)
        self.pw_entry.bind('<Return>', lambda e: self.login())

        # Boutons
        buttons_frame = tk.Frame(login_container, bg='#34495E')
        buttons_frame.pack(pady=30)

        # Bouton retour au menu principal
        if self.return_callback:
            tk.Button(
                buttons_frame,
                text="← Retour au menu",
                command=self.return_to_main_menu,
                font=('Arial', 12, 'bold'),
                bg='#95A5A6',
                fg='white',
                padx=25,
                pady=12,
                relief=tk.FLAT,
                cursor='hand2'
            ).pack(side=tk.LEFT, padx=10)

        # Bouton connexion
        tk.Button(
            buttons_frame,
            text="Se connecter",
            command=self.login,
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=30,
            pady=12,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=10)

        # Info
        tk.Label(
            login_container,
            text="⚠️ Accès réservé aux administrateurs uniquement",
            font=('Arial', 10, 'italic'),
            bg='#34495E',
            fg='#E67E22'
        ).pack(pady=(20, 0))

    def login(self):
        """Traiter la connexion"""
        username = self.user_entry.get().strip()
        password = self.pw_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return

        user = self.user_service.get_user_by_username(username)

        if not user:
            messagebox.showerror("Erreur", "Utilisateur introuvable")
            return

        if not self.encryption.verify_password(password, user.password):
            messagebox.showerror("Erreur", "Mot de passe incorrect")
            return

        if user.role != 'ADMIN':
            messagebox.showerror(
                "Accès refusé",
                "Accès refusé : seuls les administrateurs peuvent accéder à cette plateforme."
            )
            return

        if not user.is_active:
            messagebox.showerror("Erreur", "Ce compte est désactivé")
            return

        # Succès - Connexion réussie
        self.admin_user = user
        try:
            self.login_frame.pack_forget()
        except:
            pass

        self.setup_ui()
        logger.log_info(f"Panel admin ouvert par {self.admin_user.username}")

    def return_to_main_menu(self):
        """Retourner au menu principal"""
        if messagebox.askyesno("Retour", "Voulez-vous retourner au menu principal?"):
            self.root.destroy()
            if self.return_callback:
                self.return_callback()

    def setup_ui(self):
        """Configurer l'interface administrateur"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')

        # Header
        header_frame = tk.Frame(self.main_frame, bg='#2C3E50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Titre
        title_label = tk.Label(
            header_frame,
            text="🎥 PANEL ADMINISTRATEUR",
            font=('Arial', 20, 'bold'),
            bg='#2C3E50',
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=30, pady=20)

        # Info admin avec username et rôle
        admin_info = tk.Label(
            header_frame,
            text=f"👤 {self.admin_user.username} ({self.admin_user.role})",
            font=('Arial', 12),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        admin_info.pack(side=tk.RIGHT, padx=30)

        # Bouton déconnexion
        logout_btn = tk.Button(
            header_frame,
            text="🚪 Déconnexion",
            font=('Arial', 11, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2',
            relief=tk.FLAT,
            command=self.logout
        )
        logout_btn.pack(side=tk.RIGHT, padx=10)

        # Notebook (onglets)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Onglet Dashboard
        self.dashboard_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.dashboard_frame, text='📊 Tableau de bord')
        self.setup_dashboard()

        # Onglet Utilisateurs
        self.users_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.users_frame, text='👥 Utilisateurs')
        self.setup_users_tab()

        # Onglet Logs
        self.logs_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.logs_frame, text='📋 Logs d\'accès')
        self.setup_logs_tab()

    def setup_dashboard(self):
        """Configurer le tableau de bord"""
        container = tk.Frame(self.dashboard_frame, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # KPIs
        kpi_frame = tk.Frame(container, bg='white')
        kpi_frame.pack(fill=tk.X, pady=(0, 20))

        total_users = self.user_service.get_user_count()
        active_users = len(self.user_service.get_all_active_users())
        total_profiles = len(self.profile_service.get_all_profiles())
        recent_logs = len(self.access_service.get_all_access_logs(50))

        self.create_kpi_card(kpi_frame, "Utilisateurs totaux", str(total_users), "#3498DB", 0)
        self.create_kpi_card(kpi_frame, "Utilisateurs actifs", str(active_users), "#2ECC71", 1)
        self.create_kpi_card(kpi_frame, "Profils faciaux", str(total_profiles), "#9B59B6", 2)
        self.create_kpi_card(kpi_frame, "Accès récents", str(recent_logs), "#E67E22", 3)

        # Activité récente
        graph_frame = tk.LabelFrame(
            container,
            text="Activité récente",
            font=('Arial', 14, 'bold'),
            bg='white',
            padx=20,
            pady=20
        )
        graph_frame.pack(fill=tk.BOTH, expand=True)

        self.create_recent_access_list(graph_frame)

    def create_kpi_card(self, parent, title, value, color, column):
        """Créer une carte KPI"""
        card = tk.Frame(parent, bg=color, relief=tk.RAISED, bd=2)
        card.grid(row=0, column=column, padx=10, sticky='ew')
        parent.grid_columnconfigure(column, weight=1)

        value_label = tk.Label(
            card,
            text=value,
            font=('Arial', 36, 'bold'),
            bg=color,
            fg='white'
        )
        value_label.pack(pady=(20, 5))

        title_label = tk.Label(
            card,
            text=title,
            font=('Arial', 12),
            bg=color,
            fg='white'
        )
        title_label.pack(pady=(0, 20))

    def create_recent_access_list(self, parent):
        """Créer la liste des accès récents"""
        list_frame = tk.Frame(parent, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('Utilisateur', 'Résultat', 'Méthode', 'Score', 'Date/Heure')
        self.access_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            height=10
        )

        for col in columns:
            self.access_tree.heading(col, text=col)
            self.access_tree.column(col, width=150)

        self.access_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.access_tree.yview)

        self.refresh_access_logs()

    def refresh_access_logs(self):
        """Rafraîchir les logs d'accès"""
        for item in self.access_tree.get_children():
            self.access_tree.delete(item)

        logs = self.access_service.get_all_access_logs(20)
        for log in logs:
            user = self.user_service.get_user_by_id(log.personne_id) if log.personne_id else None
            username = user.username if user else "Inconnu"
            score = f"{log.similarity_score:.0%}" if log.similarity_score else "-"
            tag = 'granted' if log.access_result == 'GRANTED' else 'denied'
            self.access_tree.insert('', tk.END, values=(
                username,
                log.access_result,
                log.access_method,
                score,
                log.horaire.strftime('%Y-%m-%d %H:%M:%S')
            ), tags=(tag,))

        self.access_tree.tag_configure('granted', background='#D5F4E6')
        self.access_tree.tag_configure('denied', background='#FADBD8')

    def setup_users_tab(self):
        """Configurer l'onglet des utilisateurs"""
        container = tk.Frame(self.users_frame, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg='white')
        header.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            header,
            text="Gestion des utilisateurs",
            font=('Arial', 18, 'bold'),
            bg='white'
        ).pack(side=tk.LEFT)

        add_user_btn = tk.Button(
            header,
            text="➕ Ajouter un utilisateur",
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=20,
            pady=10,
            cursor='hand2',
            relief=tk.FLAT,
            command=self.open_add_user_dialog
        )
        add_user_btn.pack(side=tk.RIGHT)

        # Recherche et filtre
        search_frame = tk.Frame(container, bg='white')
        search_frame.pack(fill=tk.X, pady=10)

        tk.Label(search_frame, text="Rechercher:", font=('Arial', 11), bg='white').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_users)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Date:", font=('Arial', 11), bg='white').pack(side=tk.LEFT, padx=10)
        self.filter_type_var = tk.StringVar(value="jour")
        ttk.Combobox(
            search_frame,
            textvariable=self.filter_type_var,
            values=["jour", "mois", "annee"],
            state="readonly",
            width=10
        ).pack(side=tk.LEFT, padx=5)

        self.filter_date_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.filter_date_var, font=('Arial', 11), width=15).pack(side=tk.LEFT,
                                                                                                     padx=5)
        tk.Button(search_frame, text="Filtrer", command=self.filter_users, font=('Arial', 11), bg='#3498DB', fg='white',
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        # Liste des utilisateurs
        list_frame = tk.Frame(container, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('ID', 'Username', 'Email', 'Rôle', 'Statut', 'Créé le', 'Profil facial')
        self.users_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set
        )

        widths = [50, 150, 200, 100, 100, 150, 120]
        for col, width in zip(columns, widths):
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=width)

        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.users_tree.yview)

        # Boutons d'action
        action_frame = tk.Frame(container, bg='white')
        action_frame.pack(fill=tk.X, pady=(10, 0))

        buttons = [
            ("🔄 Rafraîchir", self.refresh_users, '#3498DB'),
            ("✏️ Modifier", self.edit_user, '#F39C12'),
            ("📸 Photo", self.add_face_profile, '#9B59B6'),
            ("🗑️ Supprimer", self.delete_user, '#E74C3C')
        ]

        for text, cmd, color in buttons:
            tk.Button(
                action_frame,
                text=text,
                font=('Arial', 11),
                bg=color,
                fg='white',
                padx=15,
                pady=8,
                command=cmd,
                relief=tk.FLAT,
                cursor='hand2'
            ).pack(side=tk.LEFT, padx=5)

        self.refresh_users()

    def refresh_users(self):
        """Rafraîchir la liste des utilisateurs sans filtre"""
        # Réinitialiser les filtres visuellement (optionnel)
        if hasattr(self, 'user_search_var'):
            self.user_search_var.set("")
            self.user_email_var.set("")
            self.user_role_filter_var.set("TOUS")
            self.user_status_var.set("TOUS")
            self.user_profile_var.set("TOUS")
            self.user_filter_date_var.set("")

        # Charger tous les utilisateurs
        self._load_users()

    def reset_user_filters(self):
        """Réinitialiser tous les filtres utilisateurs"""
        self.user_search_var.set("")
        self.user_email_var.set("")
        self.user_role_filter_var.set("TOUS")
        self.user_status_var.set("TOUS")
        self.user_profile_var.set("TOUS")
        self.user_filter_date_var.set("")
        self.user_filter_type_var.set("jour")
        self._load_users()

    def filter_users(self, *args):
        """Filtrer les utilisateurs selon les critères"""
        self._load_users(apply_filters=True)

    def _load_users(self, apply_filters=False):
        """Charger les utilisateurs avec ou sans filtres"""
        # Effacer l'arbre
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        # Récupérer tous les utilisateurs
        all_users = self.user_service.get_all_users()

        # Appliquer les filtres si nécessaire
        if apply_filters and hasattr(self, 'user_search_var'):
            filtered_users = []
            search_text = self.user_search_var.get().lower().strip()
            email_text = self.user_email_var.get().lower().strip()
            role_filter = self.user_role_filter_var.get()
            status_filter = self.user_status_var.get()
            profile_filter = self.user_profile_var.get()
            date_filter = self.user_filter_date_var.get().strip()
            date_type = self.user_filter_type_var.get()

            for user in all_users:
                # Filtre par username
                if search_text and search_text not in (user.username or "").lower():
                    continue

                # Filtre par email
                if email_text and email_text not in (user.email or "").lower():
                    continue

                # Filtre par rôle
                if role_filter != "TOUS" and user.role != role_filter:
                    continue

                # Filtre par statut
                if status_filter == "ACTIF" and not user.is_active:
                    continue
                if status_filter == "INACTIF" and user.is_active:
                    continue

                # Filtre par profil facial
                has_profile = self.profile_service.profile_exists(user.personne_id)
                if profile_filter == "OUI" and not has_profile:
                    continue
                if profile_filter == "NON" and has_profile:
                    continue

                # Filtre par date
                if date_filter and user.created_at:
                    try:
                        if date_type == "jour":
                            if user.created_at.strftime('%Y-%m-%d') != date_filter:
                                continue
                        elif date_type == "mois":
                            if user.created_at.strftime('%Y-%m') != date_filter:
                                continue
                        elif date_type == "annee":
                            if user.created_at.strftime('%Y') != date_filter:
                                continue
                    except:
                        continue

                filtered_users.append(user)

            users_to_display = filtered_users
        else:
            users_to_display = all_users

        # Afficher les utilisateurs
        for user in users_to_display:
            has_profile = "✅ Oui" if self.profile_service.profile_exists(user.personne_id) else "❌ Non"
            status = "✅ Actif" if user.is_active else "❌ Inactif"
            self.users_tree.insert('', tk.END, values=(
                user.personne_id,
                user.username,
                user.email or "-",
                user.role,
                status,
                user.created_at.strftime('%Y-%m-%d') if user.created_at else "-",
                has_profile
            ))

        # Mettre à jour le compteur
        if hasattr(self, 'user_count_label'):
            if apply_filters:
                self.user_count_label.config(
                    text=f"📊 {len(users_to_display)} résultat(s) sur {len(all_users)} total"
                )
            else:
                self.user_count_label.config(
                    text=f"📊 {len(users_to_display)} utilisateur(s)"
                )

    def open_add_user_dialog(self):
        """Ouvrir le dialogue d'ajout avec gestion complète"""
        dialog = AddUserDialog(self.root, self.user_service, self.profile_service)

        if dialog.result:
            # Rafraîchir la liste des utilisateurs
            self.refresh_users()

            # Message de confirmation détaillé
            result = dialog.result
            profile_status = "✅ Enregistré" if result.get('has_profile') else "❌ Non enregistré"

            messagebox.showinfo(
                "✅ Utilisateur créé",
                f"L'utilisateur a été créé avec succès !\n\n"
                f"👤 Username : {result['username']}\n"
                f"🆔 ID : {result['user_id']}\n"
                f"📧 Email : {result.get('email', 'Non fourni')}\n"
                f"🎭 Rôle : {result['role']}\n"
                f"📸 Profil facial : {profile_status}\n\n"
                f"Tables mises à jour :\n"
                f"• personne (infos utilisateur)\n"
                f"• face_profiles (embeddings faciaux)"
            )

            logger.log_info(
                f"Nouvel utilisateur créé via admin : {result['username']} "
                f"(ID: {result['user_id']}, Profil: {result.get('has_profile')})"
            )

    def add_face_profile(self):
        """Ajouter/modifier profil facial"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return

        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]

        dialog = FaceCaptureDialog(self.root, user_id, username, self.profile_service, self.face_engine)
        if getattr(dialog, 'success', False):
            self.refresh_users()
            messagebox.showinfo("Succès", "Profil facial enregistré!")

    def edit_user(self):
        """Modifier un utilisateur"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return

        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]

        dialog = EditUserDialog(self.root, self.user_service, user_id)
        if getattr(dialog, 'updated', False):
            self.refresh_users()
            messagebox.showinfo("Succès", "Utilisateur modifié!")

    def delete_user(self):
        """Supprimer un utilisateur"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return

        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]

        if messagebox.askyesno("Confirmation", f"Supprimer '{username}'?"):
            if self.user_service.delete_user(user_id):
                self.refresh_users()
                messagebox.showinfo("Succès", "Utilisateur supprimé")
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer")

    def setup_logs_tab(self):
        """Configurer l'onglet des logs avec filtres"""
        container = tk.Frame(self.logs_frame, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg='white')
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            header,
            text="Historique complet des accès",
            font=('Arial', 18, 'bold'),
            bg='white'
        ).pack(side=tk.LEFT)

        # Filtres
        filter_frame = tk.Frame(container, bg='#F8F9FA', relief=tk.RAISED, bd=1)
        filter_frame.pack(fill=tk.X, pady=(0, 15), padx=5)

        filter_title = tk.Label(
            filter_frame,
            text="🔍 Filtres de recherche",
            font=('Arial', 12, 'bold'),
            bg='#F8F9FA'
        )
        filter_title.pack(pady=(10, 5))

        # Ligne 1: Username et Résultat
        filter_row1 = tk.Frame(filter_frame, bg='#F8F9FA')
        filter_row1.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(filter_row1, text="Username:", font=('Arial', 10), bg='#F8F9FA').pack(side=tk.LEFT, padx=5)
        self.log_search_var = tk.StringVar()
        tk.Entry(filter_row1, textvariable=self.log_search_var, font=('Arial', 10), width=20).pack(side=tk.LEFT, padx=5)

        tk.Label(filter_row1, text="Résultat:", font=('Arial', 10), bg='#F8F9FA').pack(side=tk.LEFT, padx=(15, 5))
        self.log_result_var = tk.StringVar(value="TOUS")
        ttk.Combobox(
            filter_row1,
            textvariable=self.log_result_var,
            values=["TOUS", "GRANTED", "DENIED"],
            state="readonly",
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(filter_row1, text="Méthode:", font=('Arial', 10), bg='#F8F9FA').pack(side=tk.LEFT, padx=(15, 5))
        self.log_method_var = tk.StringVar(value="TOUS")
        ttk.Combobox(
            filter_row1,
            textvariable=self.log_method_var,
            values=["TOUS", "FACE_ONLY", "PIN_ONLY", "FACE_AND_PIN"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT, padx=5)

        # Ligne 2: Filtres de date
        filter_row2 = tk.Frame(filter_frame, bg='#F8F9FA')
        filter_row2.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(filter_row2, text="Type de date:", font=('Arial', 10), bg='#F8F9FA').pack(side=tk.LEFT, padx=5)
        self.log_filter_type_var = tk.StringVar(value="jour")
        ttk.Combobox(
            filter_row2,
            textvariable=self.log_filter_type_var,
            values=["jour", "mois", "annee"],
            state="readonly",
            width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(filter_row2, text="Date:", font=('Arial', 10), bg='#F8F9FA').pack(side=tk.LEFT, padx=(15, 5))
        self.log_filter_date_var = tk.StringVar()
        date_entry = tk.Entry(filter_row2, textvariable=self.log_filter_date_var, font=('Arial', 10), width=15)
        date_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(
            filter_row2,
            text="Format: YYYY-MM-DD (jour), YYYY-MM (mois), YYYY (année)",
            font=('Arial', 8, 'italic'),
            bg='#F8F9FA',
            fg='#7F8C8D'
        ).pack(side=tk.LEFT, padx=10)

        # Boutons de filtre
        filter_buttons = tk.Frame(filter_frame, bg='#F8F9FA')
        filter_buttons.pack(pady=(5, 10))

        tk.Button(
            filter_buttons,
            text="🔍 Appliquer les filtres",
            command=self.filter_logs,
            font=('Arial', 10, 'bold'),
            bg='#3498DB',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            filter_buttons,
            text="🔄 Réinitialiser",
            command=self.reset_log_filters,
            font=('Arial', 10),
            bg='#95A5A6',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        # Liste des logs
        list_frame = tk.Frame(container, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True)

        vsb = tk.Scrollbar(list_frame, orient="vertical")
        hsb = tk.Scrollbar(list_frame, orient="horizontal")

        columns = ('ID', 'Utilisateur', 'Résultat', 'Méthode', 'Score', 'Date/Heure', 'Image')
        self.logs_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        widths = [50, 150, 100, 120, 120, 180, 200]
        for col, width in zip(columns, widths):
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, width=width)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.config(command=self.logs_tree.yview)
        hsb.config(command=self.logs_tree.xview)

        # Boutons d'action
        action_frame = tk.Frame(container, bg='white')
        action_frame.pack(pady=(15, 0))

        tk.Button(
            action_frame,
            text="🔄 Rafraîchir tout",
            font=('Arial', 11, 'bold'),
            bg='#3498DB',
            fg='white',
            padx=20,
            pady=10,
            command=self.refresh_logs,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        # Compteur de résultats
        self.log_count_label = tk.Label(
            action_frame,
            text="",
            font=('Arial', 10),
            bg='white',
            fg='#7F8C8D'
        )
        self.log_count_label.pack(side=tk.LEFT, padx=20)

        self.refresh_logs()

    def refresh_logs(self):
        """Rafraîchir tous les logs sans filtre"""
        # Réinitialiser les filtres
        if hasattr(self, 'log_search_var'):
            self.log_search_var.set("")
            self.log_result_var.set("TOUS")
            self.log_method_var.set("TOUS")
            self.log_filter_date_var.set("")

        # Charger tous les logs
        self._load_logs()

    def filter_logs(self):
        """Appliquer les filtres aux logs"""
        self._load_logs(apply_filters=True)

    def reset_log_filters(self):
        """Réinitialiser tous les filtres des logs"""
        self.log_search_var.set("")
        self.log_result_var.set("TOUS")
        self.log_method_var.set("TOUS")
        self.log_filter_date_var.set("")
        self.log_filter_type_var.set("jour")
        self._load_logs()

    def _load_logs(self, apply_filters=False):
        """Charger les logs avec ou sans filtres"""
        # Effacer l'arbre
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)

        # Récupérer tous les logs
        all_logs = self.access_service.get_all_access_logs(500)  # Plus de logs pour filtrage

        # Appliquer les filtres si nécessaire
        if apply_filters and hasattr(self, 'log_search_var'):
            filtered_logs = []
            search_text = self.log_search_var.get().lower().strip()
            result_filter = self.log_result_var.get()
            method_filter = self.log_method_var.get()
            date_filter = self.log_filter_date_var.get().strip()
            date_type = self.log_filter_type_var.get()

            for log in all_logs:
                # Récupérer l'utilisateur
                user = self.user_service.get_user_by_id(log.personne_id) if log.personne_id else None
                username = user.username.lower() if user else "inconnu"

                # Filtre par username
                if search_text and search_text not in username:
                    continue

                # Filtre par résultat
                if result_filter != "TOUS" and log.access_result != result_filter:
                    continue

                # Filtre par méthode
                if method_filter != "TOUS" and log.access_method != method_filter:
                    continue

                # Filtre par date
                if date_filter and log.horaire:
                    try:
                        if date_type == "jour":
                            if log.horaire.strftime('%Y-%m-%d') != date_filter:
                                continue
                        elif date_type == "mois":
                            if log.horaire.strftime('%Y-%m') != date_filter:
                                continue
                        elif date_type == "annee":
                            if log.horaire.strftime('%Y') != date_filter:
                                continue
                    except:
                        continue

                filtered_logs.append(log)

            logs_to_display = filtered_logs
        else:
            logs_to_display = all_logs

        # Afficher les logs
        for log in logs_to_display:
            user = self.user_service.get_user_by_id(log.personne_id) if log.personne_id else None
            username = user.username if user else "Inconnu"
            score = f"{log.similarity_score:.2%}" if log.similarity_score else "-"
            image_url = log.image_url or "-"
            tag = 'granted' if log.access_result == 'GRANTED' else 'denied'

            self.logs_tree.insert('', tk.END, values=(
                log.access_id,
                username,
                log.access_result,
                log.access_method,
                score,
                log.horaire.strftime('%Y-%m-%d %H:%M:%S'),
                image_url
            ), tags=(tag,))

        self.logs_tree.tag_configure('granted', background='#D5F4E6')
        self.logs_tree.tag_configure('denied', background='#FADBD8')

        # Mettre à jour le compteur
        if hasattr(self, 'log_count_label'):
            if apply_filters:
                self.log_count_label.config(
                    text=f"📊 {len(logs_to_display)} résultat(s) trouvé(s) sur {len(all_logs)} total"
                )
            else:
                self.log_count_label.config(
                    text=f"📊 {len(logs_to_display)} log(s) affiché(s)"
                )

    def logout(self):
        """Déconnexion - retour au formulaire de connexion"""
        if messagebox.askyesno("Confirmation", "Voulez-vous vous déconnecter?"):
            self.admin_user = None
            try:
                self.main_frame.pack_forget()
            except:
                pass
            self.show_login_form()
            logger.log_info("Admin déconnecté")

    def on_close(self):
        """Gestionnaire de fermeture de la fenêtre admin"""
        if messagebox.askyesno("Quitter", "Voulez-vous quitter le panel administrateur?"):
            self.root.destroy()
            if self.return_callback:
                self.return_callback()


# Dialogues auxiliaires (simplifiés)
class AddUserDialog:
    """Dialogue d'ajout d'utilisateur avec extraction obligatoire des embeddings"""

    def __init__(self, parent, user_service, profile_service):
        self.user_service = user_service
        self.profile_service = profile_service
        self.result = None
        self.photo_path = None
        self.embeddings = None  # Stockage des embeddings extraits

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ajouter un utilisateur")
        self.dialog.geometry("500x550")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.dialog.wait_window()

    def setup_ui(self):
        main = tk.Frame(self.dialog, padx=25, pady=25)
        main.pack(fill=tk.BOTH, expand=True)

        # Titre
        title = tk.Label(
            main,
            text="➕ NOUVEL UTILISATEUR",
            font=('Arial', 16, 'bold'),
            fg='#2C3E50'
        )
        title.pack(pady=(0, 20))

        # Frame formulaire
        form_frame = tk.Frame(main)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Champs obligatoires
        fields = [
            ("Username *:", "username", False),
            ("Email:", "email", False),
            ("Password *:", "password", True),
        ]

        self.entries = {}
        row = 0
        for label_text, key, is_password in fields:
            tk.Label(
                form_frame,
                text=label_text,
                font=('Arial', 11, 'bold')
            ).grid(row=row, column=0, sticky=tk.W, pady=10, padx=(0, 10))

            entry = tk.Entry(form_frame, font=('Arial', 11), width=28)
            if is_password:
                entry.config(show="*")
            entry.grid(row=row, column=1, pady=10)
            self.entries[key] = entry
            row += 1

        # Rôle
        tk.Label(
            form_frame,
            text="Rôle *:",
            font=('Arial', 11, 'bold')
        ).grid(row=row, column=0, sticky=tk.W, pady=10, padx=(0, 10))

        self.role_var = tk.StringVar(value="USER")
        role_combo = ttk.Combobox(
            form_frame,
            textvariable=self.role_var,
            values=["USER", "ADMIN", "GUEST"],
            state="readonly",
            width=25,
            font=('Arial', 11)
        )
        role_combo.grid(row=row, column=1, pady=10)
        row += 1

        # Séparateur
        separator = tk.Frame(main, height=2, bg='#BDC3C7')
        separator.pack(fill=tk.X, pady=15)

        # Section photo (OBLIGATOIRE)
        photo_frame = tk.LabelFrame(
            main,
            text="📸 Photo du visage (OBLIGATOIRE)",
            font=('Arial', 12, 'bold'),
            fg='#E74C3C',
            padx=15,
            pady=15
        )
        photo_frame.pack(fill=tk.X, pady=(0, 15))

        # Info importante
        info_label = tk.Label(
            photo_frame,
            text="⚠️ La photo est obligatoire pour extraire les embeddings faciaux",
            font=('Arial', 9, 'italic'),
            fg='#E67E22',
            wraplength=420,
            justify=tk.LEFT
        )
        info_label.pack(pady=(0, 10))

        # Champ photo
        photo_input_frame = tk.Frame(photo_frame)
        photo_input_frame.pack(fill=tk.X)

        self.photo_entry = tk.Entry(
            photo_input_frame,
            font=('Arial', 10),
            state='readonly',
            width=35
        )
        self.photo_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            photo_input_frame,
            text="📁 Parcourir",
            command=self.select_and_extract_photo,
            font=('Arial', 10, 'bold'),
            bg='#3498DB',
            fg='white',
            padx=15,
            pady=5,
            cursor='hand2',
            relief=tk.FLAT
        ).pack(side=tk.LEFT)

        # Label statut extraction
        self.extraction_status = tk.Label(
            photo_frame,
            text="",
            font=('Arial', 9),
            wraplength=420,
            justify=tk.LEFT
        )
        self.extraction_status.pack(pady=(10, 0))

        # Boutons d'action
        btn_frame = tk.Frame(main)
        btn_frame.pack(pady=(10, 0))

        tk.Button(
            btn_frame,
            text="❌ Annuler",
            bg='#95A5A6',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            cursor='hand2',
            relief=tk.FLAT,
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="✅ Créer l'utilisateur",
            bg='#27AE60',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10,
            cursor='hand2',
            relief=tk.FLAT,
            command=self.create_user
        ).pack(side=tk.LEFT, padx=5)

        # Note en bas
        note = tk.Label(
            main,
            text="* Champs obligatoires",
            font=('Arial', 8, 'italic'),
            fg='#7F8C8D'
        )
        note.pack(pady=(10, 0))

    def select_and_extract_photo(self):
        """Sélectionner une photo et extraire immédiatement les embeddings"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner une photo du visage",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Tous les fichiers", "*.*")
            ]
        )

        if not file_path:
            return

        # Afficher le chemin
        self.photo_entry.config(state='normal')
        self.photo_entry.delete(0, tk.END)
        self.photo_entry.insert(0, file_path)
        self.photo_entry.config(state='readonly')

        # Statut en cours
        self.extraction_status.config(
            text="🔄 Extraction des embeddings en cours...",
            fg='#F39C12'
        )
        self.dialog.update()

        # Extraire les embeddings
        try:
            import face_recognition
            import os

            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                raise Exception("Le fichier n'existe pas")

            # Charger l'image
            image = face_recognition.load_image_file(file_path)

            # Détecter les visages
            face_locations = face_recognition.face_locations(image)

            if len(face_locations) == 0:
                raise Exception("Aucun visage détecté dans l'image")

            if len(face_locations) > 1:
                raise Exception(
                    f"{len(face_locations)} visages détectés. Veuillez utiliser une image avec un seul visage")

            # Extraire les embeddings
            encodings = face_recognition.face_encodings(image, face_locations)

            if not encodings or len(encodings) == 0:
                raise Exception("Impossible d'extraire les caractéristiques faciales")

            # Stocker les embeddings
            self.embeddings = encodings[0].tolist()
            self.photo_path = file_path

            # Statut succès
            self.extraction_status.config(
                text=f"✅ Embeddings extraits avec succès ! ({len(self.embeddings)} caractéristiques)",
                fg='#27AE60'
            )

            logger.log_info(f"Embeddings extraits avec succès : {len(self.embeddings)} caractéristiques")

        except ImportError:
            messagebox.showerror(
                "Erreur - Bibliothèque manquante",
                "La bibliothèque 'face_recognition' n'est pas installée.\n\n"
                "Installation requise :\n"
                "pip install face_recognition\n"
                "pip install dlib\n"
                "pip install cmake"
            )
            self.extraction_status.config(
                text="❌ Erreur : Bibliothèque 'face_recognition' manquante",
                fg='#E74C3C'
            )
            self.embeddings = None
            self.photo_path = None

        except Exception as e:
            messagebox.showerror(
                "Erreur d'extraction",
                f"Impossible d'extraire les embeddings :\n\n{str(e)}\n\n"
                "Conseils :\n"
                "- Utilisez une photo claire et bien éclairée\n"
                "- Assurez-vous qu'un seul visage est visible\n"
                "- Le visage doit être de face et bien visible"
            )
            self.extraction_status.config(
                text=f"❌ Erreur : {str(e)}",
                fg='#E74C3C'
            )
            self.embeddings = None
            self.photo_path = None
            logger.log_error(f"Erreur extraction embeddings : {e}")

    def create_user(self):
        """Créer l'utilisateur avec validation stricte"""
        # Récupérer les valeurs
        username = self.entries['username'].get().strip()
        email = self.entries['email'].get().strip() or None
        password = self.entries['password'].get().strip()
        role = self.role_var.get()

        # Validation des champs obligatoires
        if not username:
            messagebox.showerror("Erreur", "Le nom d'utilisateur est obligatoire")
            self.entries['username'].focus()
            return

        if not password:
            messagebox.showerror("Erreur", "Le mot de passe est obligatoire")
            self.entries['password'].focus()
            return

        # VALIDATION STRICTE : La photo est obligatoire
        if not self.photo_path or not self.embeddings:
            messagebox.showerror(
                "Photo obligatoire",
                "⚠️ La photo du visage est OBLIGATOIRE !\n\n"
                "Les embeddings faciaux doivent être extraits pour créer un utilisateur.\n\n"
                "Veuillez sélectionner une photo claire du visage."
            )
            return

        # Validation de la longueur du mot de passe
        if len(password) < 4:
            messagebox.showerror(
                "Mot de passe trop court",
                "Le mot de passe doit contenir au moins 4 caractères"
            )
            self.entries['password'].focus()
            return

        # Confirmation
        confirm = messagebox.askyesno(
            "Confirmer la création",
            f"Créer l'utilisateur avec ces informations ?\n\n"
            f"Username : {username}\n"
            f"Email : {email or 'Non fourni'}\n"
            f"Rôle : {role}\n"
            f"Photo : ✅ Embeddings extraits ({len(self.embeddings)} caractéristiques)\n\n"
            f"Les données seront enregistrées dans :\n"
            f"- Table 'personne' (infos utilisateur)\n"
            f"- Table 'face_profiles' (embeddings faciaux)"
        )

        if not confirm:
            return

        try:
            # ÉTAPE 1 : Créer l'utilisateur dans la table 'personne'
            logger.log_info(f"Création de l'utilisateur '{username}' dans la table 'personne'...")
            user_id = self.user_service.create_user(username, password, email, role)

            if not user_id:
                raise Exception("Impossible de créer l'utilisateur dans la table 'personne'")

            logger.log_info(f"✅ Utilisateur créé avec ID: {user_id}")

            # ÉTAPE 2 : Créer le profil facial dans la table 'face_profiles'
            logger.log_info(f"Enregistrement des embeddings dans la table 'face_profiles'...")

            # Les embeddings sont déjà une liste, les convertir en array numpy
            import numpy as np
            embedding_array = np.array(self.embeddings)

            # Créer le profil facial (lien avec personne via user_id)
            profile_created = self.profile_service.create_profile(
                personne_id=user_id,
                embedding=embedding_array,  # ← Passer directement l'array numpy
                image_url=self.photo_path
            )

            if not profile_created:
                # Si le profil échoue, on pourrait supprimer l'utilisateur créé
                logger.log_warning(f"Échec création profil pour user_id={user_id}")
                messagebox.showwarning(
                    "Avertissement",
                    "L'utilisateur a été créé mais le profil facial n'a pas pu être enregistré.\n\n"
                    "Vous pouvez réessayer d'ajouter la photo via 'Modifier'."
                )
            else:
                logger.log_info(f"✅ Profil facial créé avec succès pour user_id={user_id}")

            # SUCCÈS COMPLET
            self.result = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'has_profile': profile_created
            }

            messagebox.showinfo(
                "✅ Succès",
                f"Utilisateur créé avec succès !\n\n"
                f"👤 Username : {username}\n"
                f"🆔 ID : {user_id}\n"
                f"📧 Email : {email or 'Non fourni'}\n"
                f"🎭 Rôle : {role}\n"
                f"📸 Profil facial : {'✅ Enregistré' if profile_created else '❌ Échec'}\n\n"
                f"Les données ont été enregistrées dans :\n"
                f"• Table 'personne' (infos utilisateur)\n"
                f"• Table 'face_profiles' (embeddings faciaux)"
            )

            self.dialog.destroy()

        except Exception as e:
            logger.log_error(f"Erreur lors de la création de l'utilisateur : {e}")
            messagebox.showerror(
                "Erreur",
                f"Impossible de créer l'utilisateur :\n\n{str(e)}\n\n"
                f"Causes possibles :\n"
                f"- Le nom d'utilisateur existe déjà\n"
                f"- Problème de connexion à la base de données\n"
                f"- Erreur d'enregistrement du profil facial"
            )


class EditUserDialog:
    """Dialogue de modification d'utilisateur"""

    def __init__(self, parent, user_service, user_id):
        self.user_service = user_service
        self.user = user_service.get_user_by_id(user_id)
        self.updated = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Modifier utilisateur")
        self.dialog.geometry("450x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.dialog.wait_window()

    def setup_ui(self):
        main = tk.Frame(self.dialog, padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="Username:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=10)
        tk.Label(main, text=self.user.username if self.user else "", font=('Arial', 11)).grid(row=0, column=1,
                                                                                              sticky=tk.W, pady=10)

        tk.Label(main, text="Email:", font=('Arial', 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.email_entry = tk.Entry(main, font=('Arial', 11), width=30)
        self.email_entry.grid(row=1, column=1, pady=10)
        self.email_entry.insert(0, self.user.email or "")

        tk.Label(main, text="Rôle:", font=('Arial', 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.role_var = tk.StringVar(value=self.user.role if self.user else "USER")
        ttk.Combobox(main, textvariable=self.role_var, values=["USER", "ADMIN", "GUEST"], state="readonly",
                     width=27).grid(row=2, column=1, pady=10)

        tk.Label(main, text="Actif (1/0):", font=('Arial', 11)).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.active_var = tk.StringVar(value="1" if (self.user.is_active if self.user else False) else "0")
        tk.Entry(main, textvariable=self.active_var, font=('Arial', 11), width=30).grid(row=3, column=1, pady=10)

        btn_frame = tk.Frame(main)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=30)

        tk.Button(btn_frame, text="Annuler", bg="#95A5A6", fg="white", padx=20, pady=10,
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Enregistrer", bg="#27AE60", fg="white", padx=20, pady=10, command=self.save).pack(
            side=tk.LEFT, padx=5)

    def save(self):
        email = self.email_entry.get().strip()
        role = self.role_var.get()
        is_active = self.active_var.get() == "1"

        try:
            self.user_service.update_user(self.user.personne_id, email=email, role=role, is_active=is_active)
            self.updated = True
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de mettre à jour: {e}")
        finally:
            self.dialog.destroy()


class FaceCaptureDialog:
    """Dialogue de capture de profil facial"""

    def __init__(self, parent, user_id, username, profile_service, face_engine):
        self.success = False
        self.user_id = user_id
        self.username = username
        self.profile_service = profile_service
        self.face_engine = face_engine

        if messagebox.askyesno("Profil facial", f"Capturer le profil facial pour {username}?"):
            try:
                img_path = filedialog.askopenfilename(
                    title="Sélectionner une photo",
                    filetypes=[("Images", "*.jpg *.png *.jpeg")]
                )

                if img_path:
                    try:
                        import face_recognition
                        image = face_recognition.load_image_file(img_path)
                        encodings = face_recognition.face_encodings(image)

                        if encodings:
                            embedding = json.dumps(encodings[0].tolist())
                            self.profile_service.create_profile(
                                self.user_id,
                                embedding=embedding,
                                image_url=img_path
                            )
                            messagebox.showinfo("Succès", "Profil facial enregistré!")
                            self.success = True
                        else:
                            messagebox.showwarning("Avertissement", "Aucun visage détecté dans l'image")
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Erreur extraction: {e}")
                else:
                    messagebox.showinfo("Info", "Aucune image sélectionnée")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur: {e}")


def launch_admin_panel():
    """Fonction pour lancer le panel admin (compatibilité)"""
    db = DatabaseConnection()
    db.connect()

    face_engine = FaceRecognitionEngine()
    user_service = UserService(db)
    profile_service = ProfileService(db)
    access_service = AccessService(db)

    AdminWindow(
        db=db,
        face_engine=face_engine,
        user_service=user_service,
        profile_service=profile_service,
        access_service=access_service
    )


if __name__ == "__main__":
    launch_admin_panel()