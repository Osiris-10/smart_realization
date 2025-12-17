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

        # === ZONE DE FILTRAGE ===
        filter_frame = tk.Frame(container, bg='#f0f0f0', relief=tk.GROOVE, bd=1)
        filter_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Ligne de filtres
        filter_row = tk.Frame(filter_frame, bg='#f0f0f0')
        filter_row.pack(fill=tk.X, padx=10, pady=10)

        # Champ recherche
        tk.Label(filter_row, text="🔍 Rechercher:", font=('Arial', 11, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0,5))
        self.entry_recherche = tk.Entry(filter_row, font=('Arial', 11), width=25)
        self.entry_recherche.pack(side=tk.LEFT, padx=(0,20))

        # Champ date
        tk.Label(filter_row, text="📅 Date (YYYY-MM-DD):", font=('Arial', 11, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0,5))
        self.entry_date = tk.Entry(filter_row, font=('Arial', 11), width=15)
        self.entry_date.pack(side=tk.LEFT, padx=(0,20))

        # Bouton Filtrer
        btn_filtrer = tk.Button(
            filter_row, 
            text="🔍 FILTRER", 
            font=('Arial', 11, 'bold'),
            bg='#2980B9', 
            fg='white',
            padx=20, 
            pady=5,
            cursor='hand2',
            command=self.appliquer_filtre
        )
        btn_filtrer.pack(side=tk.LEFT, padx=5)

        # Bouton Reset
        btn_reset = tk.Button(
            filter_row, 
            text="↺ RESET", 
            font=('Arial', 11),
            bg='#7F8C8D', 
            fg='white',
            padx=15, 
            pady=5,
            cursor='hand2',
            command=self.reset_filtre
        )
        btn_reset.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter pour filtrer
        self.entry_recherche.bind('<Return>', lambda e: self.appliquer_filtre())
        self.entry_date.bind('<Return>', lambda e: self.appliquer_filtre())

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
        """Rafraîchir la liste - afficher tous les utilisateurs"""
        self.entry_recherche.delete(0, tk.END)
        self.entry_date.delete(0, tk.END)
        self.charger_tous_utilisateurs()

    def charger_tous_utilisateurs(self):
        """Charger et afficher tous les utilisateurs"""
        # Vider le tableau
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Charger tous les utilisateurs
        users = self.user_service.get_all_users()
        
        # Afficher
        for user in users:
            self.ajouter_ligne_utilisateur(user)
        
        logger.log_info(f"{len(users)} utilisateurs affichés")

    def ajouter_ligne_utilisateur(self, user):
        """Ajouter une ligne utilisateur au tableau"""
        has_profile = "✅ Oui" if self.profile_service.profile_exists(user.personne_id) else "❌ Non"
        status = "✅ Actif" if user.is_active else "❌ Inactif"
        date_str = user.created_at.strftime('%Y-%m-%d') if user.created_at else "-"
        
        self.users_tree.insert('', tk.END, values=(
            user.personne_id,
            user.username,
            user.email or "-",
            user.role,
            status,
            date_str,
            has_profile
        ))

    def appliquer_filtre(self):
        """Appliquer le filtre de recherche"""
        # Lire les valeurs des champs
        texte_recherche = self.entry_recherche.get().strip().lower()
        date_recherche = self.entry_date.get().strip()
        
        logger.log_info(f"FILTRE: texte='{texte_recherche}', date='{date_recherche}'")
        
        # Vider le tableau
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Charger tous les utilisateurs
        tous_users = self.user_service.get_all_users()
        
        # Si aucun filtre, afficher tout
        if not texte_recherche and not date_recherche:
            for user in tous_users:
                self.ajouter_ligne_utilisateur(user)
            logger.log_info(f"Aucun filtre - {len(tous_users)} utilisateurs")
            return
        
        # Filtrer
        count = 0
        for user in tous_users:
            # Vérifier texte (username ou email)
            if texte_recherche:
                username = (user.username or "").lower()
                email = (user.email or "").lower()
                if texte_recherche not in username and texte_recherche not in email:
                    continue
            
            # Vérifier date
            if date_recherche and user.created_at:
                date_user = user.created_at.strftime('%Y-%m-%d')
                if date_recherche not in date_user:
                    continue
            
            # Utilisateur correspond aux critères
            self.ajouter_ligne_utilisateur(user)
            count += 1
        
        logger.log_info(f"RÉSULTAT: {count} utilisateur(s) sur {len(tous_users)}")

    def reset_filtre(self):
        """Réinitialiser les filtres"""
        self.entry_recherche.delete(0, tk.END)
        self.entry_date.delete(0, tk.END)
        self.charger_tous_utilisateurs()

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
        """Configurer l'onglet des logs d'accès"""
        container = tk.Frame(self.logs_frame, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        tk.Label(
            container,
            text="📋 Historique des accès",
            font=('Arial', 18, 'bold'),
            bg='white'
        ).pack(anchor='w', pady=(0, 15))

        # === ZONE DE FILTRAGE ===
        filter_frame = tk.Frame(container, bg='#f0f0f0', relief=tk.GROOVE, bd=1)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        filter_row = tk.Frame(filter_frame, bg='#f0f0f0')
        filter_row.pack(fill=tk.X, padx=10, pady=10)

        # Username
        tk.Label(filter_row, text="👤 Username:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0,5))
        self.log_entry_username = tk.Entry(filter_row, font=('Arial', 10), width=15)
        self.log_entry_username.pack(side=tk.LEFT, padx=(0,15))

        # Résultat
        tk.Label(filter_row, text="✓ Résultat:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0,5))
        self.log_combo_resultat = ttk.Combobox(filter_row, values=["TOUS", "GRANTED", "DENIED"], state="readonly", width=10)
        self.log_combo_resultat.set("TOUS")
        self.log_combo_resultat.pack(side=tk.LEFT, padx=(0,15))

        # Date
        tk.Label(filter_row, text="📅 Date:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0,5))
        self.log_entry_date = tk.Entry(filter_row, font=('Arial', 10), width=12)
        self.log_entry_date.pack(side=tk.LEFT, padx=(0,15))

        # Boutons
        tk.Button(filter_row, text="🔍 FILTRER", font=('Arial', 10, 'bold'), bg='#2980B9', fg='white',
                  padx=15, pady=3, command=self.appliquer_filtre_logs).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_row, text="↺ RESET", font=('Arial', 10), bg='#7F8C8D', fg='white',
                  padx=10, pady=3, command=self.reset_filtre_logs).pack(side=tk.LEFT, padx=5)

        # Bind Enter
        self.log_entry_username.bind('<Return>', lambda e: self.appliquer_filtre_logs())
        self.log_entry_date.bind('<Return>', lambda e: self.appliquer_filtre_logs())

        # === TABLEAU DES LOGS ===
        list_frame = tk.Frame(container, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('ID', 'Utilisateur', 'Résultat', 'Méthode', 'Score', 'Date/Heure')
        self.logs_tree = ttk.Treeview(list_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)

        widths = [50, 150, 100, 120, 100, 180]
        for col, width in zip(columns, widths):
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, width=width)

        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.logs_tree.yview)

        # Tags pour coloration
        self.logs_tree.tag_configure('granted', background='#D5F4E6')
        self.logs_tree.tag_configure('denied', background='#FADBD8')

        # Charger les logs
        self.charger_tous_logs()

    def charger_tous_logs(self):
        """Charger et afficher tous les logs"""
        # Vider le tableau
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        
        # Charger les logs
        logs = self.access_service.get_all_access_logs(500)
        
        # Afficher
        for log in logs:
            self.ajouter_ligne_log(log)
        
        logger.log_info(f"{len(logs)} logs affichés")

    def ajouter_ligne_log(self, log):
        """Ajouter une ligne de log au tableau"""
        user = self.user_service.get_user_by_id(log.personne_id) if log.personne_id else None
        username = user.username if user else "Inconnu"
        score = f"{log.similarity_score:.2%}" if log.similarity_score else "-"
        date_str = log.horaire.strftime('%Y-%m-%d %H:%M:%S') if log.horaire else "-"
        tag = 'granted' if log.access_result == 'GRANTED' else 'denied'
        
        self.logs_tree.insert('', tk.END, values=(
            log.access_id,
            username,
            log.access_result,
            log.access_method,
            score,
            date_str
        ), tags=(tag,))

    def appliquer_filtre_logs(self):
        """Appliquer les filtres aux logs"""
        # Lire les valeurs
        username_filtre = self.log_entry_username.get().strip().lower()
        resultat_filtre = self.log_combo_resultat.get()
        date_filtre = self.log_entry_date.get().strip()
        
        logger.log_info(f"FILTRE LOGS: username='{username_filtre}', resultat='{resultat_filtre}', date='{date_filtre}'")
        
        # Vider le tableau
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        
        # Charger tous les logs
        tous_logs = self.access_service.get_all_access_logs(500)
        
        # Si aucun filtre, afficher tout
        if not username_filtre and resultat_filtre == "TOUS" and not date_filtre:
            for log in tous_logs:
                self.ajouter_ligne_log(log)
            logger.log_info(f"Aucun filtre - {len(tous_logs)} logs")
            return
        
        # Filtrer
        count = 0
        for log in tous_logs:
            # Vérifier username
            if username_filtre:
                user = self.user_service.get_user_by_id(log.personne_id) if log.personne_id else None
                username = (user.username if user else "").lower()
                if username_filtre not in username:
                    continue
            
            # Vérifier résultat
            if resultat_filtre != "TOUS" and log.access_result != resultat_filtre:
                continue
            
            # Vérifier date
            if date_filtre and log.horaire:
                date_log = log.horaire.strftime('%Y-%m-%d')
                if date_filtre not in date_log:
                    continue
            
            # Log correspond aux critères
            self.ajouter_ligne_log(log)
            count += 1
        
        logger.log_info(f"RÉSULTAT: {count} log(s) sur {len(tous_logs)}")

    def reset_filtre_logs(self):
        """Réinitialiser les filtres des logs"""
        self.log_entry_username.delete(0, tk.END)
        self.log_combo_resultat.set("TOUS")
        self.log_entry_date.delete(0, tk.END)
        self.charger_tous_logs()

    def refresh_logs(self):
        """Rafraîchir les logs (compatibilité)"""
        self.reset_filtre_logs()

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

        if not self.user:
            messagebox.showerror("Erreur", "Utilisateur introuvable")
            return

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"✏️ Modifier - {self.user.username}")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='#ECF0F1')

        self.setup_ui()
        self.dialog.wait_window()

    def setup_ui(self):
        # Debug: afficher les vraies valeurs
        print(f"\n>>> OUVERTURE FORMULAIRE EDIT")
        print(f"    User ID: {self.user.personne_id}")
        print(f"    Username: {self.user.username}")
        print(f"    Role BDD: '{self.user.role}'")
        print(f"    is_active BDD: {self.user.is_active} (type: {type(self.user.is_active).__name__})")
        
        # Header
        header = tk.Frame(self.dialog, bg='#3498DB', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"✏️ Modifier l'utilisateur",
            font=('Arial', 16, 'bold'),
            bg='#3498DB',
            fg='white'
        ).pack(pady=15)

        # Formulaire
        form = tk.Frame(self.dialog, bg='#ECF0F1', padx=30, pady=20)
        form.pack(fill=tk.BOTH, expand=True)

        # Username (modifiable)
        tk.Label(form, text="👤 Username:", font=('Arial', 11, 'bold'), bg='#ECF0F1').grid(row=0, column=0, sticky=tk.W, pady=10)
        self.username_entry = tk.Entry(form, font=('Arial', 12), width=30)
        self.username_entry.grid(row=0, column=1, pady=10, padx=10)
        self.username_entry.insert(0, self.user.username or "")

        # Email
        tk.Label(form, text="📧 Email:", font=('Arial', 11, 'bold'), bg='#ECF0F1').grid(row=1, column=0, sticky=tk.W, pady=10)
        self.email_entry = tk.Entry(form, font=('Arial', 12), width=30)
        self.email_entry.grid(row=1, column=1, pady=10, padx=10)
        self.email_entry.insert(0, self.user.email or "")

        # Rôle - utiliser la vraie valeur
        tk.Label(form, text="🎭 Rôle:", font=('Arial', 11, 'bold'), bg='#ECF0F1').grid(row=2, column=0, sticky=tk.W, pady=10)
        current_role = self.user.role if self.user.role else "USER"
        self.role_combo = ttk.Combobox(form, values=["USER", "ADMIN", "GUEST"], state="readonly", width=28, font=('Arial', 11))
        self.role_combo.grid(row=2, column=1, pady=10, padx=10)
        self.role_combo.set(current_role)

        # Statut actif - utiliser Combobox comme pour le rôle
        tk.Label(form, text="✓ Statut:", font=('Arial', 11, 'bold'), bg='#ECF0F1').grid(row=3, column=0, sticky=tk.W, pady=10)
        current_active = bool(self.user.is_active) if self.user.is_active is not None else True
        current_status = "Actif" if current_active else "Inactif"
        self.status_combo = ttk.Combobox(form, values=["Actif", "Inactif"], state="readonly", width=28, font=('Arial', 11))
        self.status_combo.grid(row=3, column=1, pady=10, padx=10)
        self.status_combo.set(current_status)
        print(f"    status_combo initialisé à: {current_status}")

        # Nouveau mot de passe (optionnel)
        tk.Label(form, text="🔐 Nouveau mot de passe:", font=('Arial', 11, 'bold'), bg='#ECF0F1').grid(row=4, column=0, sticky=tk.W, pady=10)
        self.password_entry = tk.Entry(form, font=('Arial', 12), width=30, show='*')
        self.password_entry.grid(row=4, column=1, pady=10, padx=10)
        
        tk.Label(form, text="(laisser vide pour ne pas changer)", font=('Arial', 9, 'italic'), bg='#ECF0F1', fg='#7F8C8D').grid(row=5, column=1, sticky=tk.W, padx=10)

        # Boutons
        btn_frame = tk.Frame(self.dialog, bg='#ECF0F1', pady=20)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame,
            text="❌ Annuler",
            font=('Arial', 11, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=25,
            pady=10,
            cursor='hand2',
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=30)

        tk.Button(
            btn_frame,
            text="✅ Enregistrer",
            font=('Arial', 11, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=25,
            pady=10,
            cursor='hand2',
            command=self.save
        ).pack(side=tk.RIGHT, padx=30)

    def save(self):
        """Sauvegarder les modifications"""
        new_username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        role = self.role_combo.get()
        status = self.status_combo.get()
        is_active = (status == "Actif")  # Convertir en bool
        print(f"    status_combo.get() = '{status}' -> is_active = {is_active}")
        new_password = self.password_entry.get().strip()

        print("\n" + "="*60)
        print("       MODIFICATION UTILISATEUR - DEBUG")
        print("="*60)
        print(f"ID Utilisateur: {self.user.personne_id}")
        print("-"*60)
        print("VALEURS ACTUELLES (avant modification):")
        print(f"  Username: {self.user.username}")
        print(f"  Email: {self.user.email}")
        print(f"  Role: {self.user.role}")
        print(f"  Actif: {self.user.is_active}")
        print("-"*60)
        print("NOUVELLES VALEURS (formulaire):")
        print(f"  Username: {new_username}")
        print(f"  Email: {email}")
        print(f"  Role: {role}")
        print(f"  Actif: {is_active}")
        print(f"  Nouveau MDP: {'OUI (****)' if new_password else 'NON (inchangé)'}")
        print("-"*60)

        # Validation
        if not new_username:
            messagebox.showerror("Erreur", "Le username ne peut pas être vide!")
            return

        # Vérifier si le nouveau username existe déjà (si changé)
        if new_username != self.user.username:
            existing = self.user_service.get_user_by_username(new_username)
            if existing:
                messagebox.showerror("Erreur", f"Le username '{new_username}' existe déjà!")
                return

        try:
            # Préparer les données à mettre à jour
            update_data = {
                'username': new_username,
                'email': email,
                'role': role,
                'is_active': bool(is_active)
            }
            
            # Ajouter le mot de passe si fourni
            if new_password:
                update_data['password'] = new_password

            print("DONNÉES ENVOYÉES À update_user():")
            for k, v in update_data.items():
                if k == 'password':
                    print(f"  {k}: ****")
                else:
                    print(f"  {k}: {v}")

            # Mettre à jour
            success = self.user_service.update_user(self.user.personne_id, **update_data)
            
            print("-"*60)
            print(f"RÉSULTAT: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
            print("="*60 + "\n")
            
            if success:
                self.updated = True
                messagebox.showinfo("✅ Succès", f"L'utilisateur '{new_username}' a été modifié avec succès!")
            else:
                messagebox.showerror("Erreur", "Impossible de mettre à jour l'utilisateur")
                
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            print("="*60 + "\n")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur lors de la modification:\n{str(e)}")
        finally:
            self.dialog.destroy()


class FaceCaptureDialog:
    """Dialogue pour ajouter/modifier un profil facial via photo"""

    def __init__(self, parent, user_id, username, profile_service, face_engine):
        self.success = False
        self.user_id = user_id
        self.username = username
        self.profile_service = profile_service
        self.face_engine = face_engine
        self.parent = parent

        # Vérifier si un profil existe déjà
        existing_profile = self.profile_service.get_profile_by_user(user_id)
        
        if existing_profile:
            action = messagebox.askyesnocancel(
                "Profil existant",
                f"L'utilisateur '{username}' a déjà un profil facial.\n\n"
                "Voulez-vous le remplacer par une nouvelle photo ?\n\n"
                "• Oui = Remplacer le profil\n"
                "• Non = Supprimer le profil\n"
                "• Annuler = Ne rien faire"
            )
            
            if action is None:  # Annuler
                return
            elif action is False:  # Non = Supprimer
                if self.profile_service.delete_profile(existing_profile.profile_id):
                    messagebox.showinfo("Succès", "Profil facial supprimé!")
                    self.success = True
                return
            # Si Oui, continuer pour remplacer
        
        # Sélectionner une photo
        self.selectionner_photo(existing_profile)

    def selectionner_photo(self, existing_profile=None):
        """Ouvrir le dialogue de sélection de photo"""
        img_path = filedialog.askopenfilename(
            parent=self.parent,
            title=f"Sélectionner une photo pour {self.username}",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Tous les fichiers", "*.*")
            ]
        )

        if not img_path:
            messagebox.showinfo("Info", "Aucune image sélectionnée")
            return

        # Extraire les embeddings
        self.extraire_et_sauvegarder(img_path, existing_profile)

    def extraire_et_sauvegarder(self, img_path, existing_profile=None):
        """Extraire les embeddings de la photo et les sauvegarder"""
        try:
            import face_recognition
            import numpy as np
            
            logger.log_info(f"Chargement de l'image: {img_path}")
            
            # Charger l'image
            image = face_recognition.load_image_file(img_path)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                messagebox.showwarning(
                    "Aucun visage détecté",
                    "Aucun visage n'a été détecté dans cette image.\n\n"
                    "Conseils :\n"
                    "• Utilisez une photo de face\n"
                    "• Assurez-vous que le visage est bien éclairé\n"
                    "• Évitez les photos floues"
                )
                return
            
            if len(face_locations) > 1:
                messagebox.showwarning(
                    "Plusieurs visages",
                    f"{len(face_locations)} visages détectés.\n"
                    "Seul le premier visage sera utilisé.\n\n"
                    "Pour de meilleurs résultats, utilisez une photo avec un seul visage."
                )
            
            # Extraire les encodings (embeddings)
            encodings = face_recognition.face_encodings(image, face_locations)
            
            if not encodings:
                messagebox.showerror("Erreur", "Impossible d'extraire les caractéristiques du visage")
                return
            
            # Prendre le premier encoding (numpy array de 128 dimensions)
            embedding = encodings[0]
            
            logger.log_info(f"Embedding extrait: {embedding.shape} dimensions")
            
            # Sauvegarder dans la base de données
            if existing_profile:
                # Mettre à jour le profil existant
                success = self.profile_service.update_profile(
                    profile_id=existing_profile.profile_id,
                    embedding=embedding,
                    image_url=img_path
                )
                if success:
                    messagebox.showinfo(
                        "✅ Profil mis à jour",
                        f"Le profil facial de '{self.username}' a été mis à jour avec succès!"
                    )
                    self.success = True
                    logger.log_info(f"Profil mis à jour pour {self.username} (ID: {self.user_id})")
                else:
                    messagebox.showerror("Erreur", "Impossible de mettre à jour le profil")
            else:
                # Créer un nouveau profil
                profile_id = self.profile_service.create_profile(
                    personne_id=self.user_id,
                    embedding=embedding,
                    image_url=img_path
                )
                if profile_id:
                    messagebox.showinfo(
                        "✅ Profil créé",
                        f"Le profil facial de '{self.username}' a été créé avec succès!\n\n"
                        f"ID du profil: {profile_id}"
                    )
                    self.success = True
                    logger.log_info(f"Nouveau profil créé pour {self.username} (ID: {self.user_id}, Profile: {profile_id})")
                else:
                    messagebox.showerror("Erreur", "Impossible de créer le profil facial")
                    
        except ImportError:
            messagebox.showerror(
                "Module manquant",
                "Le module 'face_recognition' n'est pas installé.\n\n"
                "Installez-le avec: pip install face_recognition"
            )
        except Exception as e:
            logger.log_error(f"Erreur extraction embedding: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction:\n{str(e)}")


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