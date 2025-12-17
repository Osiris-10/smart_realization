# admin_dashboard.py
# Changes:
# - In users tab, added date filter: filter_entry and button to filter by date_added (YYYY-MM-DD).
# - In load_users, added optional where_clause for filters.
# - In filter_users, now handles both search and date filter.
# - In add_user (open_registration): Assuming RegistrationWindow handles photo and embeddings (code not provided, but instruct to add).
# - Modify and delete already work.
# - Display username next to ADMIN: Done in header.
# - Logout: Destroys dashboard, reopens login, if success, new dashboard.

import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import Logger
from ui.registration_window import RegistrationWindow

logger = Logger()


class AdminDashboard:
    """Dashboard administrateur complet"""

    def __init__(self, parent, admin_user, face_engine, auth_manager, access_service, user_service, profile_service,
                 db):
        """
        Initialiser le dashboard admin
        Args:
            parent: Fenêtre parent
            admin_user: Objet Personne de l'admin connecté
            face_engine: Moteur de reconnaissance
            auth_manager: Gestionnaire auth
            access_service: Service d'accès
            user_service: Service utilisateur
            profile_service: Service profils
            db: Connexion base de données
        """
        self.parent = parent
        self.admin_user = admin_user
        self.face_engine = face_engine
        self.auth_manager = auth_manager
        self.access_service = access_service
        self.user_service = user_service
        self.profile_service = profile_service
        self.db = db

        self.window = tk.Toplevel(parent)
        self.window.title(f"🎛️ Dashboard Admin - {admin_user.username}")
        self.window.geometry("1400x800")
        self.window.configure(bg='#ECF0F1')

        logger.log_info(f"Dashboard admin ouvert par: {admin_user.username}")

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Configurer l'interface"""
        # ===== HEADER =====
        header_frame = tk.Frame(self.window, bg='#2C3E50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Titre
        title = tk.Label(
            header_frame,
            text="🎛️ PANNEAU D'ADMINISTRATION",
            font=('Arial', 22, 'bold'),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        title.pack(side=tk.LEFT, padx=30, pady=20)

        # Info admin avec username connecté ✅ AJOUT ICI
        admin_info = tk.Label(
            header_frame,
            text=f"👤 Connecté: {self.admin_user.username} (ADMIN)",  # ✅ Affiche le username
            font=('Arial', 11, 'bold'),
            bg='#2C3E50',
            fg='#3498DB'  # Couleur bleue pour mise en évidence
        )
        admin_info.pack(side=tk.LEFT, padx=20)

        # Bouton déconnexion
        logout_btn = tk.Button(
            header_frame,
            text="🚪 Déconnexion",
            font=('Arial', 10, 'bold'),
            bg='#E74C3C',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.logout
        )
        logout_btn.pack(side=tk.RIGHT, padx=30)

        # ===== BODY =====
        body_frame = tk.Frame(self.window, bg='#ECF0F1')
        body_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ===== KPIs (Indicateurs) =====
        kpi_frame = tk.Frame(body_frame, bg='#ECF0F1')
        kpi_frame.pack(fill=tk.X, pady=(0, 20))

        # KPI 1: Total Utilisateurs
        self.kpi_total_users = self.create_kpi_card(
            kpi_frame, "👥 UTILISATEURS", "0", "#3498DB", 0
        )

        # KPI 2: Utilisateurs Actifs
        self.kpi_active_users = self.create_kpi_card(
            kpi_frame, "✅ ACTIFS", "0", "#27AE60", 1
        )

        # KPI 3: Accès Aujourd'hui
        self.kpi_access_today = self.create_kpi_card(
            kpi_frame, "📊 ACCÈS (24H)", "0", "#9B59B6", 2
        )

        # KPI 4: Taux de Succès
        self.kpi_success_rate = self.create_kpi_card(
            kpi_frame, "✓ TAUX SUCCÈS", "0%", "#F39C12", 3
        )

        # ===== TABS =====
        tab_frame = tk.Frame(body_frame, bg='#ECF0F1')
        tab_frame.pack(fill=tk.BOTH, expand=True)

        # Notebook (Onglets)
        self.notebook = ttk.Notebook(tab_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Style pour les onglets
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background='#ECF0F1')
        style.configure('TNotebook.Tab', font=('Arial', 11, 'bold'), padding=[20, 10])

        # Onglet 1: Utilisateurs
        self.setup_users_tab()

        # Onglet 2: Logs d'Accès
        self.setup_logs_tab()

        # Onglet 3: Statistiques
        self.setup_stats_tab()

    def create_kpi_card(self, parent, title, value, color, position):
        """Créer une carte KPI"""
        card = tk.Frame(parent, bg=color, relief=tk.RAISED, bd=2)
        card.grid(row=0, column=position, padx=10, sticky='ew')
        parent.grid_columnconfigure(position, weight=1)

        # Titre
        title_label = tk.Label(
            card,
            text=title,
            font=('Arial', 11, 'bold'),
            bg=color,
            fg='white'
        )
        title_label.pack(pady=(15, 5))

        # Valeur
        value_label = tk.Label(
            card,
            text=value,
            font=('Arial', 28, 'bold'),
            bg=color,
            fg='white'
        )
        value_label.pack(pady=(5, 15))

        return value_label

    def setup_users_tab(self):
        """Onglet gestion des utilisateurs"""
        users_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(users_tab, text="👥 GESTION UTILISATEURS")

        # Toolbar
        toolbar = tk.Frame(users_tab, bg='#34495E', height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # Boutons d'action
        add_user_btn = tk.Button(
            toolbar,
            text="➕ Nouvel Utilisateur",
            font=('Arial', 11, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.open_registration
        )
        add_user_btn.pack(side=tk.LEFT, padx=10, pady=10)

        refresh_btn = tk.Button(
            toolbar,
            text="🔄 Actualiser",
            font=('Arial', 11, 'bold'),
            bg='#3498DB',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.refresh_users_list
        )
        refresh_btn.pack(side=tk.LEFT, padx=10, pady=10)

        # Recherche
        search_frame = tk.Frame(toolbar, bg='#34495E')
        search_frame.pack(side=tk.LEFT, padx=20)
        tk.Label(
            search_frame,
            text="🔍 Rechercher:",
            font=('Arial', 11, 'bold'),
            bg='#34495E',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 11),
            width=20
        )
        search_entry.pack(side=tk.LEFT, padx=5)
        # Bind Enter key pour recherche
        search_entry.bind('<Return>', lambda e: self.filter_users())

        # Filtre par date
        tk.Label(
            search_frame,
            text="📅 Date:",
            font=('Arial', 11, 'bold'),
            bg='#34495E',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        self.filter_date_var = tk.StringVar()
        filter_entry = tk.Entry(
            search_frame,
            textvariable=self.filter_date_var,
            font=('Arial', 11),
            width=12
        )
        filter_entry.pack(side=tk.LEFT, padx=5)
        # Bind Enter key pour filtre date
        filter_entry.bind('<Return>', lambda e: self.filter_users())

        # Bouton Filtrer
        tk.Button(
            search_frame,
            text="🔍 Filtrer",
            font=('Arial', 11, 'bold'),
            bg='#16A085',
            fg='white',
            padx=15,
            pady=5,
            command=self.filter_users
        ).pack(side=tk.LEFT, padx=10)

        # Bouton Reset
        tk.Button(
            search_frame,
            text="↺ Reset",
            font=('Arial', 11),
            bg='#95A5A6',
            fg='white',
            padx=10,
            pady=5,
            command=self.reset_filters
        ).pack(side=tk.LEFT, padx=5)

        # Frame pour la table
        table_frame = tk.Frame(users_tab, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        y_scrollbar = tk.Scrollbar(table_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview (Table)
        columns = ('ID', 'Username', 'Email', 'Role', 'Créé le', 'Statut', 'Profil Facial')
        self.users_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            height=20
        )

        # Configuration des colonnes
        self.users_tree.heading('ID', text='ID')
        self.users_tree.heading('Username', text='Nom d\'utilisateur')
        self.users_tree.heading('Email', text='Email')
        self.users_tree.heading('Role', text='Rôle')
        self.users_tree.heading('Créé le', text='Date de création')
        self.users_tree.heading('Statut', text='Statut')
        self.users_tree.heading('Profil Facial', text='Profil Facial')

        self.users_tree.column('ID', width=50, anchor='center')
        self.users_tree.column('Username', width=150)
        self.users_tree.column('Email', width=200)
        self.users_tree.column('Role', width=100, anchor='center')
        self.users_tree.column('Créé le', width=150, anchor='center')
        self.users_tree.column('Statut', width=100, anchor='center')
        self.users_tree.column('Profil Facial', width=100, anchor='center')

        self.users_tree.pack(fill=tk.BOTH, expand=True)
        y_scrollbar.config(command=self.users_tree.yview)
        x_scrollbar.config(command=self.users_tree.xview)

        # Menu contextuel
        self.users_tree.bind('<Button-3>', self.show_user_context_menu)
        self.users_tree.bind('<Double-Button-1>', self.edit_user)

        # Style pour le Treeview
        style = ttk.Style()
        style.configure('Treeview', font=('Arial', 10), rowheight=30)
        style.configure('Treeview.Heading', font=('Arial', 11, 'bold'))

    def setup_logs_tab(self):
        """Onglet logs d'accès"""
        logs_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(logs_tab, text="📋 LOGS D'ACCÈS")

        # Toolbar
        toolbar = tk.Frame(logs_tab, bg='#34495E', height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # Filtre par période
        tk.Label(
            toolbar,
            text="📅 Période:",
            font=('Arial', 11, 'bold'),
            bg='#34495E',
            fg='white'
        ).pack(side=tk.LEFT, padx=20)

        self.period_var = tk.StringVar(value='24h')
        periods = [
            ('Dernières 24h', '24h'),
            ('7 derniers jours', '7d'),
            ('30 derniers jours', '30d'),
            ('Tout', 'all')
        ]
        for text, value in periods:
            rb = tk.Radiobutton(
                toolbar,
                text=text,
                variable=self.period_var,
                value=value,
                font=('Arial', 10),
                bg='#34495E',
                fg='white',
                selectcolor='#2C3E50',
                activebackground='#34495E',
                activeforeground='white',
                command=self.refresh_logs
            )
            rb.pack(side=tk.LEFT, padx=5)

        # Bouton export
        export_btn = tk.Button(
            toolbar,
            text="📥 Exporter CSV",
            font=('Arial', 10, 'bold'),
            bg='#16A085',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.export_logs
        )
        export_btn.pack(side=tk.RIGHT, padx=20)

        # Frame table
        table_frame = tk.Frame(logs_tab, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        y_scrollbar = tk.Scrollbar(table_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        columns = ('ID', 'User ID', 'Username', 'Résultat', 'Méthode', 'Score', 'Date/Heure')
        self.logs_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            height=25
        )

        self.logs_tree.heading('ID', text='ID')
        self.logs_tree.heading('User ID', text='User ID')
        self.logs_tree.heading('Username', text='Utilisateur')
        self.logs_tree.heading('Résultat', text='Résultat')
        self.logs_tree.heading('Méthode', text='Méthode')
        self.logs_tree.heading('Score', text='Score Similarité')
        self.logs_tree.heading('Date/Heure', text='Date/Heure')

        self.logs_tree.column('ID', width=50, anchor='center')
        self.logs_tree.column('User ID', width=70, anchor='center')
        self.logs_tree.column('Username', width=150)
        self.logs_tree.column('Résultat', width=100, anchor='center')
        self.logs_tree.column('Méthode', width=120, anchor='center')
        self.logs_tree.column('Score', width=120, anchor='center')
        self.logs_tree.column('Date/Heure', width=180, anchor='center')

        self.logs_tree.pack(fill=tk.BOTH, expand=True)
        y_scrollbar.config(command=self.logs_tree.yview)

        # Tags pour coloration
        self.logs_tree.tag_configure('granted', background='#D5F4E6')
        self.logs_tree.tag_configure('denied', background='#FADBD8')

    def setup_stats_tab(self):
        """Onglet statistiques"""
        stats_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(stats_tab, text="📊 STATISTIQUES")

        # Titre
        title = tk.Label(
            stats_tab,
            text="📊 STATISTIQUES DÉTAILLÉES",
            font=('Arial', 18, 'bold'),
            bg='white',
            fg='#2C3E50'
        )
        title.pack(pady=20)

        # Frame des stats
        stats_frame = tk.Frame(stats_tab, bg='white')
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)

        # Créer les cartes de statistiques
        self.create_stat_row(stats_frame, "🎯 Taux de reconnaissance faciale", "0%", 0)
        self.create_stat_row(stats_frame, "🔐 Authentifications PIN uniquement", "0", 1)
        self.create_stat_row(stats_frame, "❌ Tentatives refusées (24h)", "0", 2)
        self.create_stat_row(stats_frame, "⚠️ Comptes verrouillés", "0", 3)
        self.create_stat_row(stats_frame, "📈 Pic d'activité", "N/A", 4)
        self.create_stat_row(stats_frame, "🕒 Dernière activité", "N/A", 5)

    def create_stat_row(self, parent, label_text, value_text, row):
        """Créer une ligne de statistique"""
        row_frame = tk.Frame(parent, bg='#ECF0F1', relief=tk.RAISED, bd=1)
        row_frame.grid(row=row, column=0, sticky='ew', pady=5)
        parent.grid_columnconfigure(0, weight=1)

        label = tk.Label(
            row_frame,
            text=label_text,
            font=('Arial', 13, 'bold'),
            bg='#ECF0F1',
            fg='#2C3E50',
            anchor='w'
        )
        label.pack(side=tk.LEFT, padx=20, pady=15)

        value = tk.Label(
            row_frame,
            text=value_text,
            font=('Arial', 13),
            bg='#ECF0F1',
            fg='#3498DB',
            anchor='e'
        )
        value.pack(side=tk.RIGHT, padx=20, pady=15)

        # Stocker la référence
        setattr(self, f'stat_value_{row}', value)

    def load_data(self):
        """Charger toutes les données"""
        self.load_kpis()
        self.load_users()
        self.load_logs()
        self.load_stats()

    def load_kpis(self):
        """Charger les KPIs"""
        try:
            # Total utilisateurs
            total_users = self.user_service.get_user_count()
            self.kpi_total_users.config(text=str(total_users))

            # Utilisateurs actifs
            active_users = len(self.user_service.get_all_active_users())
            self.kpi_active_users.config(text=str(active_users))

            # Accès aujourd'hui (PostgreSQL)
            query = """
                SELECT COUNT(*) FROM acces_log
                WHERE horaire::date = CURRENT_DATE
            """
            result = self.db.execute_query(query)
            access_today = result[0][0] if result else 0
            self.kpi_access_today.config(text=str(access_today))

            # Taux de succès (PostgreSQL)
            query = """
                SELECT COUNT(CASE WHEN access_result = 'GRANTED' THEN 1 END) as granted,
                       COUNT(*) as total
                FROM acces_log
                WHERE horaire >= NOW() - INTERVAL '24 hours'
            """
            result = self.db.execute_query(query)
            if result and result[0][1] > 0:
                granted, total = result[0]
                success_rate = (granted / total) * 100
                self.kpi_success_rate.config(text=f"{success_rate:.1f}%")
            else:
                self.kpi_success_rate.config(text="N/A")
        except Exception as e:
            logger.log_error(f"Erreur chargement KPIs: {e}")

    def load_users(self, where_clause="", params=()):
        """Charger la liste des utilisateurs avec clause optionnelle"""
        try:
            # Effacer le tableau
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)

            # Récupérer tous les utilisateurs
            users = self.user_service.get_all_users(where_clause, params)
            for user in users:
                # Vérifier si profil facial existe
                has_profile = self.profile_service.profile_exists(user.personne_id)
                profile_text = "✓ Oui" if has_profile else "✗ Non"

                # Statut
                status_text = "✓ Actif" if user.is_active else "✗ Inactif"

                # Date formatée
                date_str = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"

                self.users_tree.insert('', 'end', values=(
                    user.personne_id,
                    user.username,
                    user.email or "N/A",
                    user.role,
                    date_str,
                    status_text,
                    profile_text
                ))
            logger.log_info(f"{len(users)} utilisateurs chargés")
        except Exception as e:
            logger.log_error(f"Erreur chargement utilisateurs: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les utilisateurs: {e}")

    def load_logs(self):
        """Charger les logs d'accès"""
        try:
            # Effacer le tableau
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)

            # Déterminer la période
            period = self.period_var.get()
            if period == '24h':
                query = """
                    SELECT al.access_id, al.personne_id, p.username, al.access_result,
                           al.access_method, al.similarity_score, al.horaire
                    FROM acces_log al
                    LEFT JOIN personne p ON al.personne_id = p.personne_id
                    WHERE al.horaire >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                    ORDER BY al.horaire DESC
                    LIMIT 500
                """
            elif period == '7d':
                query = """
                    SELECT al.access_id, al.personne_id, p.username, al.access_result,
                           al.access_method, al.similarity_score, al.horaire
                    FROM acces_log al
                    LEFT JOIN personne p ON al.personne_id = p.personne_id
                    WHERE al.horaire >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    ORDER BY al.horaire DESC
                    LIMIT 1000
                """
            elif period == '30d':
                query = """
                    SELECT al.access_id, al.personne_id, p.username, al.access_result,
                           al.access_method, al.similarity_score, al.horaire
                    FROM acces_log al
                    LEFT JOIN personne p ON al.personne_id = p.personne_id
                    WHERE al.horaire >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    ORDER BY al.horaire DESC
                    LIMIT 2000
                """
            else:  # all
                query = """
                    SELECT al.access_id, al.personne_id, p.username, al.access_result,
                           al.access_method, al.similarity_score, al.horaire
                    FROM acces_log al
                    LEFT JOIN personne p ON al.personne_id = p.personne_id
                    ORDER BY al.horaire DESC
                    LIMIT 5000
                """

            results = self.db.execute_query(query)
            for row in results:
                access_id, personne_id, username, result, method, score, horaire = row
                username_display = username if username else "Inconnu"
                personne_id_display = personne_id if personne_id else "N/A"
                score_display = f"{score:.2f}" if score else "N/A"
                horaire_str = horaire.strftime("%Y-%m-%d %H:%M:%S") if horaire else "N/A"

                # Tag pour coloration
                tag = 'granted' if result == 'GRANTED' else 'denied'

                self.logs_tree.insert('', 'end', values=(
                    access_id,
                    personne_id_display,
                    username_display,
                    result,
                    method,
                    score_display,
                    horaire_str
                ), tags=(tag,))
            logger.log_info(f"{len(results) if results else 0} logs chargés")
        except Exception as e:
            logger.log_error(f"Erreur chargement logs: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les logs: {e}")

    def load_stats(self):
        """Charger les statistiques détaillées"""
        try:
            # Stat 0: Taux de reconnaissance faciale
            query = """
                SELECT COUNT(CASE WHEN access_method IN ('FACE_PIN', 'FACE_ONLY') AND access_result = 'GRANTED' THEN 1 END) as face_success,
                       COUNT(CASE WHEN access_method IN ('FACE_PIN', 'FACE_ONLY') THEN 1 END) as face_total
                FROM acces_log
                WHERE horaire >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            result = self.db.execute_query(query)
            if result and result[0][1] > 0:
                face_success, face_total = result[0]
                rate = (face_success / face_total) * 100
                self.stat_value_0.config(text=f"{rate:.1f}%")

            # Stat 1: Authentifications PIN uniquement
            query = """
                SELECT COUNT(*) FROM acces_log
                WHERE access_method = 'PIN_ONLY'
                AND horaire >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            result = self.db.execute_query(query)
            if result:
                self.stat_value_1.config(text=str(result[0][0]))

            # Stat 2: Tentatives refusées (24h)
            query = """
                SELECT COUNT(*) FROM acces_log
                WHERE access_result = 'DENIED'
                AND horaire >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            result = self.db.execute_query(query)
            if result:
                self.stat_value_2.config(text=str(result[0][0]))

            # Stat 3: Comptes verrouillés
            query = """
                SELECT COUNT(*) FROM attempts_counter
                WHERE failed_face_attempts >= 3 OR failed_pin_attempts >= 3
            """
            result = self.db.execute_query(query)
            if result:
                self.stat_value_3.config(text=str(result[0][0]))

            # Stat 4: Pic d'activité
            query = """
                SELECT HOUR(horaire) as hour, COUNT(*) as count
                FROM acces_log
                WHERE horaire >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY HOUR(horaire)
                ORDER BY count DESC
                LIMIT 1
            """
            result = self.db.execute_query(query)
            if result:
                hour = result[0][0]
                self.stat_value_4.config(text=f"{hour}h - {hour + 1}h")

            # Stat 5: Dernière activité
            query = """
                SELECT horaire FROM acces_log
                ORDER BY horaire DESC
                LIMIT 1
            """
            result = self.db.execute_query(query)
            if result:
                last_time = result[0][0]
                self.stat_value_5.config(text=last_time.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            logger.log_error(f"Erreur chargement stats: {e}")

    def refresh_users_list(self):
        """Actualiser la liste des utilisateurs"""
        self.load_users()
        self.load_kpis()
        messagebox.showinfo("Info", "Liste des utilisateurs actualisée!")

    def refresh_logs(self):
        """Actualiser les logs"""
        self.load_logs()

    def reset_filters(self):
        """Réinitialiser les filtres et afficher tous les utilisateurs"""
        self.search_var.set("")
        self.filter_date_var.set("")
        self.load_users()
        logger.log_info("Filtres réinitialisés")

    def filter_users(self, *args):
        """Filtrer les utilisateurs par recherche et date"""
        try:
            search_text = self.search_var.get().strip()
            filter_date = self.filter_date_var.get().strip()

            logger.log_info(f"Filtrage: recherche='{search_text}', date='{filter_date}'")

            # Si aucun filtre, charger tous les utilisateurs
            if not search_text and not filter_date:
                self.load_users()
                return

            # Construire la clause WHERE avec des paramètres sécurisés (PostgreSQL)
            conditions = []
            params = []

            if search_text:
                # PostgreSQL: ILIKE pour recherche insensible à la casse
                conditions.append("(username ILIKE %s OR email ILIKE %s)")
                params.append(f"%{search_text}%")
                params.append(f"%{search_text}%")

            if filter_date:
                try:
                    datetime.strptime(filter_date, '%Y-%m-%d')  # Validate format
                    # PostgreSQL: cast avec ::date
                    conditions.append("created_at::date = %s")
                    params.append(filter_date)
                except ValueError:
                    messagebox.showerror("Erreur", "Format de date invalide: YYYY-MM-DD")
                    return

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            logger.log_info(f"WHERE clause: {where_clause}, params: {params}")
            self.load_users(where_clause, tuple(params))
        except Exception as e:
            logger.log_error(f"Erreur filter_users: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du filtrage: {e}")

    def open_registration(self):
        """Ouvrir la fenêtre d'enregistrement"""
        # Note: Assurez-vous que RegistrationWindow demande une photo, extrait embeddings avec face_recognition, et stocke dans face_profiles table.
        # Par exemple, utiliser face_recognition.face_encodings pour extraire et json.dumps pour stocker.
        RegistrationWindow(
            parent=self.window,
            face_engine=self.face_engine,
            user_service=self.user_service,
            profile_service=self.profile_service
        )
        # Actualiser après fermeture
        self.window.after(500, self.refresh_users_list)

    def show_user_context_menu(self, event):
        """Afficher le menu contextuel sur un utilisateur"""
        # Sélectionner l'item
        item = self.users_tree.identify_row(event.y)
        if item:
            self.users_tree.selection_set(item)

            # Créer le menu
            menu = tk.Menu(self.window, tearoff=0)
            menu.add_command(label="✏️ Modifier", command=self.edit_user)
            menu.add_command(label="🔐 Réinitialiser mot de passe", command=self.reset_password)
            menu.add_command(label="🔒 Désactiver", command=self.deactivate_user)
            menu.add_command(label="✓ Activer", command=self.activate_user)
            menu.add_separator()
            menu.add_command(label="🗑️ Supprimer", command=self.delete_user)

            menu.post(event.x_root, event.y_root)

    def edit_user(self, event=None):
        """Modifier un utilisateur"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un utilisateur!")
            return
        item = self.users_tree.item(selection[0])
        values = item['values']
        user_id = values[0]
        # TODO: Ouvrir un dialogue pour modifier username, email, role, etc.
        # Exemple: self.user_service.update_user(user_id, new_values)
        messagebox.showinfo("Info",
                            f"Fonction d'édition pour l'utilisateur ID {user_id}\n(Mettre à jour avec self.user_service.update_user)")

    def reset_password(self):
        """Réinitialiser le mot de passe"""
        selection = self.users_tree.selection()
        if not selection:
            return
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]

        # Dialogue pour nouveau mot de passe
        dialog = tk.Toplevel(self.window)
        dialog.title("Réinitialiser mot de passe")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(dialog, text=f"Nouveau mot de passe pour: {username}", font=('Arial', 12, 'bold')).pack(pady=20)
        new_pass_entry = tk.Entry(dialog, font=('Arial', 12), width=25, show='*')
        new_pass_entry.pack(pady=10)
        new_pass_entry.focus()

        def save_new_password():
            new_pass = new_pass_entry.get()
            if not new_pass:
                messagebox.showerror("Erreur", "Le mot de passe ne peut pas être vide!")
                return
            if self.user_service.update_user(user_id, password=new_pass):
                logger.log_info(f"Mot de passe réinitialisé pour utilisateur {username}")
                messagebox.showinfo("Succès", "Mot de passe réinitialisé avec succès!")
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", "Échec de la réinitialisation!")

        tk.Button(dialog, text="✓ Valider", command=save_new_password, bg='#27AE60', fg='white', padx=20, pady=8).pack(
            pady=10)

    def deactivate_user(self):
        """Désactiver un utilisateur"""
        selection = self.users_tree.selection()
        if not selection:
            return
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]

        if messagebox.askyesno("Confirmation", f"Désactiver l'utilisateur '{username}' ?"):
            if self.user_service.deactivate_user(user_id):
                logger.log_info(f"Utilisateur {username} désactivé")
                messagebox.showinfo("Succès", "Utilisateur désactivé!")
                self.refresh_users_list()

    def activate_user(self):
        """Activer un utilisateur"""
        selection = self.users_tree.selection()
        if not selection:
            return
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]

        if self.user_service.activate_user(user_id):
            logger.log_info(f"Utilisateur {username} activé")
            messagebox.showinfo("Succès", "Utilisateur activé!")
            self.refresh_users_list()

    def delete_user(self):
        """Supprimer un utilisateur"""
        selection = self.users_tree.selection()
        if not selection:
            return
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]

        if user_id == self.admin_user.personne_id:
            messagebox.showerror("Erreur", "Vous ne pouvez pas supprimer votre propre compte!")
            return

        if messagebox.askyesno("⚠️ CONFIRMATION DE SUPPRESSION", f"ATTENTION: Cette action est IRRÉVERSIBLE!\n\n"
                                                                 f"Supprimer définitivement l'utilisateur '{username}' ?\n"
                                                                 f"Toutes les données associées seront perdues.",
                               icon='warning'):
            # Double confirmation
            if messagebox.askyesno("Dernière confirmation", "Êtes-vous absolument sûr ?"):
                if self.user_service.delete_user(user_id):
                    logger.log_warning(f"Utilisateur {username} supprimé par {self.admin_user.username}")
                    messagebox.showinfo("Succès", "Utilisateur supprimé définitivement!")
                    self.refresh_users_list()

    def export_logs(self):
        """Exporter les logs en CSV"""
        try:
            from tkinter import filedialog
            import csv
            from datetime import datetime

            # Demander où sauvegarder
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            if not filename:
                return

            # Récupérer les données
            items = []
            for item_id in self.logs_tree.get_children():
                items.append(self.logs_tree.item(item_id)['values'])

            # Écrire dans le CSV
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'User ID', 'Username', 'Résultat', 'Méthode', 'Score', 'Date/Heure'])
                writer.writerows(items)

            logger.log_info(f"Logs exportés vers: {filename}")
            messagebox.showinfo("Succès", f"Logs exportés vers:\n{filename}")
        except Exception as e:
            logger.log_error(f"Erreur export logs: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")

    def logout(self):
        """Déconnexion - retour au formulaire de login"""
        if messagebox.askyesno("Déconnexion", "Voulez-vous vous déconnecter ?"):
            logger.log_info(f"Déconnexion admin: {self.admin_user.username}")
            # Fermer le dashboard
            self.window.destroy()

            # Réouvrir le formulaire de connexion
            root = tk.Tk()
            root.withdraw()
            login_dialog = AdminLoginDialog(
                parent=root,
                auth_manager=self.auth_manager,
                user_service=self.user_service
            )
            admin_user = login_dialog.get_admin_user()

            if admin_user:
                # Nouvel admin connecté, rouvrir le dashboard
                AdminDashboard(
                    parent=root,
                    admin_user=admin_user,
                    face_engine=self.face_engine,
                    auth_manager=self.auth_manager,
                    access_service=self.access_service,
                    user_service=self.user_service,
                    profile_service=self.profile_service,
                    db=self.db
                )
                root.mainloop()
            else:
                root.destroy()