# ui/camera_widget.py - VERSION QUI MARCHE VRAIMENT
"""Widget caméra - Version finale qui marche"""
import tkinter as tk
from PIL import Image, ImageTk
import cv2
from typing import Callable, Optional
from utils.logger import Logger
from config.settings import CAMERA_INDEX, CAMERA_FLIP

logger = Logger()

class CameraWidget:
    """Widget caméra stable"""

    def __init__(self, parent, process_callback: Optional[Callable] = None):
        self.parent = parent
        self.process_callback = process_callback

        # Label
        self.label = tk.Label(parent, bg='black', text='🎥 Initialisation...',
                             fg='white', font=('Arial', 14))
        self.label.pack(fill=tk.BOTH, expand=True)

        # Compatibilité
        self.canvas = self.label
        self.video_label = self.label

        self.cap = None
        self.is_running = False
        self.current_frame = None
        self._photo = None

        logger.log_info("CameraWidget initialisé")

    def start(self):
        """Démarrer la caméra"""
        try:
            logger.log_info(f"Ouverture caméra {CAMERA_INDEX}...")

            self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(CAMERA_INDEX)

            if not self.cap.isOpened():
                logger.log_error("❌ Caméra inaccessible")
                self.label.config(text='❌ Caméra inaccessible', fg='red')
                return False

            ret, test = self.cap.read()
            if not ret or test is None:
                logger.log_error("❌ Lecture impossible")
                self.cap.release()
                self.label.config(text='❌ Lecture impossible', fg='red')
                return False

            logger.log_info(f"✅ Caméra OK: {test.shape}")

            self.is_running = True

            # 🔥 ATTENDRE QUE LE WIDGET SOIT RÉALISÉ
            self.label.update_idletasks()  # Force Tkinter à créer le widget

            # Démarrer après 300ms pour laisser le temps à Tkinter
            self.label.after(300, self._loop)

            logger.log_info("✅ Boucle programmée")
            return True

        except Exception as e:
            logger.log_error(f"❌ Erreur start: {e}")
            import traceback
            logger.log_error(traceback.format_exc())
            self.label.config(text=f'❌ Erreur: {str(e)[:50]}', fg='red')
            return False

    def stop(self):
        """Arrêter"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self._photo = None
        try:
            self.label.config(text='📹 Caméra arrêtée', fg='white')
        except:
            pass
        logger.log_info("Caméra arrêtée")

    def _loop(self):
        """Boucle d'affichage"""
        if not self.is_running:
            logger.log_debug("Boucle arrêtée")
            return

        # Vérifier existence
        try:
            if not self.label.winfo_exists():
                logger.log_debug("Label détruit")
                self.is_running = False
                return
        except:
            self.is_running = False
            return

        try:
            # Lire frame
            ret, frame = self.cap.read()

            if not ret or frame is None:
                logger.log_warning("Frame non lue")
                self.label.after(100, self._loop)
                return

            # Flip
            if CAMERA_FLIP:
                frame = cv2.flip(frame, 1)

            # Sauvegarder
            self.current_frame = frame.copy()

            # Callback
            if self.process_callback:
                try:
                    frame = self.process_callback(frame)
                except Exception as e:
                    logger.log_error(f"Callback erreur: {e}")
                    cv2.putText(frame, "Erreur callback", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Convertir
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, (640, 480))

            # PIL
            pil_img = Image.fromarray(resized)

            # 🔥 CRÉER PhotoImage AVEC master=self.label
            self._photo = ImageTk.PhotoImage(image=pil_img, master=self.label)

            # Afficher
            self.label.config(image=self._photo, text='')

            # Continuer
            if self.is_running:
                self.label.after(33, self._loop)

            logger.log_debug("Frame affichée OK")

        except tk.TclError as e:
            logger.log_error(f"TclError: {e}")
            # Ne pas arrêter, réessayer
            if self.is_running:
                self.label.after(200, self._loop)
        except Exception as e:
            logger.log_error(f"Erreur loop: {e}")
            import traceback
            logger.log_error(traceback.format_exc())

            try:
                self.label.config(text=f'❌ {str(e)[:50]}', fg='red')
            except:
                pass

            # Réessayer
            if self.is_running:
                self.label.after(100, self._loop)

    def get_current_frame(self):
        """Frame actuel"""
        return self.current_frame.copy() if self.current_frame is not None else None

    def capture_image(self):
        """Capturer"""
        return self.get_current_frame()