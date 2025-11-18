"""Panel d'affichage des statuts"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime


class StatusPanel:
    """Panel pour afficher les statuts et informations"""

    def __init__(self, parent):
        """
        Initialiser le panel de statuts

        Args:
            parent: Widget parent Tkinter
        """
        self.parent = parent

        # Frame principal
        self.main_frame = tk.Frame(parent, bg='white')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titre
        title = tk.Label(
            self.main_frame,
            text="📊 STATUT DU SYSTÈME",
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#2C3E50'
        )
        title.pack(pady=10)

        # Séparateur
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=10)

        # Status actuel
        status_frame = tk.Frame(self.main_frame, bg='white')
        status_frame.pack(fill='x', pady=10)

        tk.Label(
            status_frame,
            text="Statut:",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w')

        self.status_label = tk.Label(
            status_frame,
            text="En attente...",
            font=('Arial', 11),
            bg='white',
            fg='#7F8C8D',
            wraplength=300,
            justify='left'
        )
        self.status_label.pack(anchor='w', pady=5)

        # Score de similarité
        similarity_frame = tk.Frame(self.main_frame, bg='white')
        similarity_frame.pack(fill='x', pady=10)

        tk.Label(
            similarity_frame,
            text="Score de similarité:",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w')

        self.similarity_label = tk.Label(
            similarity_frame,
            text="N/A",
            font=('Arial', 11),
            bg='white',
            fg='#7F8C8D'
        )
        self.similarity_label.pack(anchor='w', pady=5)

        # Barre de progression
        self.progress_bar = ttk.Progressbar(
            similarity_frame,
            length=300,
            mode='determinate'
        )
        self.progress_bar.pack(fill='x', pady=5)

        # Heure
        time_frame = tk.Frame(self.main_frame, bg='white')
        time_frame.pack(fill='x', pady=10)

        tk.Label(
            time_frame,
            text="Dernière tentative:",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w')

        self.time_label = tk.Label(
            time_frame,
            text="-",
            font=('Arial', 11),
            bg='white',
            fg='#7F8C8D'
        )
        self.time_label.pack(anchor='w', pady=5)

        # Historique
        history_frame = tk.Frame(self.main_frame, bg='white')
        history_frame.pack(fill='both', expand=True, pady=10)

        tk.Label(
            history_frame,
            text="Historique:",
            font=('Arial', 12, 'bold'),
            bg='white'
        ).pack(anchor='w')

        # Liste scrollable
        scrollbar = tk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(
            history_frame,
            font=('Arial', 9),
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.history_listbox.pack(fill='both', expand=True, pady=5)
        scrollbar.config(command=self.history_listbox.yview)

    def update_status(self, message: str, status_type: str = "info"):
        """
        Mettre à jour le statut

        Args:
            message: Message à afficher
            status_type: Type ('success', 'error', 'warning', 'info')
        """
        colors = {
            'success': '#00FF00',
            'error': '#FF0000',
            'warning': '#FFA500',
            'info': '#0000FF'
        }

        color = colors.get(status_type, '#0000FF')

        self.status_label.config(text=message, fg=color)
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))

        # Ajouter à l'historique
        time_str = datetime.now().strftime("%H:%M:%S")
        self.history_listbox.insert(0, f"[{time_str}] {message}")

        # Limiter à 50 entrées
        if self.history_listbox.size() > 50:
            self.history_listbox.delete(50, tk.END)

    def update_similarity(self, score: float):
        """
        Mettre à jour le score de similarité

        Args:
            score: Score entre 0 et 1
        """
        percentage = int(score * 100)
        self.similarity_label.config(text=f"{percentage}%")
        self.progress_bar['value'] = percentage

    def clear_history(self):
        """Effacer l'historique"""
        self.history_listbox.delete(0, tk.END)