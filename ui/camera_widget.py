"""Widget pour afficher le flux de la caméra"""
import tkinter as tk
from tkinter import Canvas
import cv2
from PIL import Image, ImageTk
from typing import Callable, Optional
from utils.logger import Logger
from config.settings import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, CAMERA_FLIP

logger = Logger()

class CameraWidget:
    """Widget pour gérer l'affichage de la caméra"""

    def __init__(self, parent, process_callback: Optional[Callable] = None):
        """
        Initialiser le widget caméra

        Args:
            parent: Widget parent Tkinter
            process_callback: Fonction de traitement du frame
        """
        self.parent = parent
        self.process_callback = process_callback

        self.canvas = Canvas(parent, bg='black', width=640, height=480)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.cap = None
        self.is_running = False
        self.current_frame = None

        logger.log_info("Widget caméra initialisé")

    def start(self):
        """Démarrer la capture vidéo"""
        try:
            self.cap = cv2.VideoCapture(CAMERA_INDEX)

            if not self.cap.isOpened():
                logger.log_error("Impossible d'ouvrir la caméra")
                return False

            # Configurer la caméra
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

            self.is_running = True
            self.update_frame()

            logger.log_info("Caméra démarrée")
            return True

        except Exception as e:
            logger.log_error(f"Erreur démarrage caméra: {e}")
            return False

    def stop(self):
        """Arrêter la capture vidéo"""
        self.is_running = False

        if self.cap:
            self.cap.release()
            self.cap = None

        logger.log_info("Caméra arrêtée")

    def update_frame(self):
        """Mettre à jour le frame affiché"""
        if not self.is_running or not self.cap:
            return

        try:
            ret, frame = self.cap.read()

            if ret:
                # Inverser horizontalement si configuré
                if CAMERA_FLIP:
                    frame = cv2.flip(frame, 1)

                # Traiter le frame si callback fourni
                if self.process_callback:
                    try:
                        frame = self.process_callback(frame)
                    except Exception as e:
                        logger.log_error(f"Erreur dans process_callback: {e}")

                # Convertir BGR à RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Redimensionner pour s'adapter au canvas
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                if canvas_width > 1 and canvas_height > 1:
                    frame_rgb = cv2.resize(frame_rgb, (canvas_width, canvas_height))

                # Convertir en image PIL
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)

                # Afficher sur le canvas
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.canvas.image = photo  # Garder une référence

                self.current_frame = frame

            # Planifier la prochaine mise à jour
            self.parent.after(10, self.update_frame)

        except Exception as e:
            logger.log_error(f"Erreur mise à jour frame: {e}")

    def get_current_frame(self):
        """Obtenir le frame actuel"""
        return self.current_frame

    def capture_image(self) -> Optional:
        """Capturer une image"""
        if self.current_frame is not None:
            return self.current_frame.copy()
        return None