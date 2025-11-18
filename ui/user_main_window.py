# ui/user_main_window.py
import tkinter as tk
from tkinter import messagebox
from .main_window import MainWindow  # garde ton ancienne MainWindow pour la reconnaissance

class UserMainWindow:
    def __init__(self, startup_root, **services):
        self.startup_root = startup_root
        self.services = services
        self.root = tk.Tk()
        self.root.title("Mode Utilisateur")
        self.root.geometry("500x400")
        self.root.configure(bg='#ECF0F1')
        self.setup_home()

    def setup_home(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root, bg='#ECF0F1')
        frame.pack(expand=True)

        tk.Label(frame, text="👤 MODE UTILISATEUR", font=('Arial', 24, 'bold'),
                 bg='#ECF0F1', fg='#2C3E50').pack(pady=40)

        tk.Button(frame, text="▶ DÉMARRER LA RECONNAISSANCE", font=('Arial', 16, 'bold'),
                  bg='#3498DB', fg='white', height=3, width=30,
                  command=self.start_recognition).pack(pady=30)

        tk.Button(frame, text="← Retour au menu principal", font=('Arial', 12),
                  bg='#95A5A6', fg='white',
                  command=self.back_to_startup).pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.back_to_startup)

    def start_recognition(self):
        # On réutilise ta MainWindow existante, mais on lui passe un callback de retour propre
        self.root.withdraw()
        recognition_app = MainWindow(**self.services)
        # On surcharge le bouton retour de MainWindow pour revenir ici
        def custom_return():
            recognition_app.return_to_home = self.back_to_user_home
            recognition_app.on_closing = self.back_to_startup
            recognition_app.return_to_home()

        recognition_app.return_to_home = lambda: self.back_to_user_home(recognition_app)
        recognition_app.root.protocol("WM_DELETE_WINDOW", self.back_to_startup)
        recognition_app.show_recognition_page()

    def back_to_user_home(self, recognition_app=None):
        if recognition_app and recognition_app.camera_widget:
            recognition_app.camera_widget.stop()
        self.root.deiconify()

    def back_to_startup(self):
        if messagebox.askokcancel("Retour", "Revenir au menu principal ?"):
            self.root.destroy()
            self.startup_root.deiconify()

    def run(self):
        self.root.mainloop()