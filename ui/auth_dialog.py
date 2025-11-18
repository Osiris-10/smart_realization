"""Dialogue pour demander le mot de passe/PIN"""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from utils.logger import Logger
from config.settings import PASSWORD_LENGTH

logger = Logger()


class AuthDialog:
    """Dialogue pour l'authentification"""

    def __init__(self, parent, message: str = "Entrez votre mot de passe:"):
        """
        Initialiser le dialogue

        Args:
            parent: Fenêtre parent
            message: Message à afficher
        """
        self.result = None

        # Créer la fenêtre modale
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Authentification")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)

        # Centrer la fenêtre
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Frame principal
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Message
        message_label = tk.Label(
            main_frame,
            text=message,
            font=('Arial', 12),
            wraplength=350
        )
        message_label.pack(pady=10)

        # Champ de saisie
        self.entry = tk.Entry(
            main_frame,
            show="*",
            font=('Arial', 14),
            width=20,
            justify='center'
        )
        self.entry.pack(pady=20)
        self.entry.focus()

        # Bind Enter key
        self.entry.bind('<Return>', self.on_submit)
        self.entry.bind('<KeyRelease>', self.on_key_release)

        # Frame boutons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Bouton OK
        ok_button = tk.Button(
            button_frame,
            text="OK",
            command=self.on_submit,
            font=('Arial', 10, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=20,
            pady=5,
            width=10
        )
        ok_button.pack(side=tk.LEFT, padx=5)

        # Bouton Annuler
        cancel_button = tk.Button(
            button_frame,
            text="Annuler",
            command=self.on_cancel,
            font=('Arial', 10),
            bg='#E74C3C',
            fg='white',
            padx=20,
            pady=5,
            width=10
        )
        cancel_button.pack(side=tk.LEFT, padx=5)

        logger.log_debug("Dialogue d'authentification affiché")

    def on_key_release(self, event):
        """Gestionnaire de relâchement de touche"""
        # Auto-submit si longueur atteinte
        if len(self.entry.get()) == PASSWORD_LENGTH:
            self.on_submit()

    def on_submit(self, event=None):
        """Valider la saisie"""
        self.result = self.entry.get()
        self.dialog.destroy()

    def on_cancel(self):
        """Annuler"""
        self.result = None
        self.dialog.destroy()

    def get_password(self) -> Optional[str]:
        """
        Obtenir le mot de passe saisi

        Returns:
            Mot de passe ou None si annulé
        """
        self.dialog.wait_window()
        return self.result