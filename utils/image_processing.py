"""Utilitaires pour le traitement d'images"""
import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple, Optional, Union


class ImageProcessor:
    """Classe pour traiter les images"""

    @staticmethod
    def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Redimensionner une image

        Args:
            image: Image à redimensionner
            width: Nouvelle largeur
            height: Nouvelle hauteur

        Returns:
            Image redimensionnée
        """
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    @staticmethod
    def resize_keep_aspect(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
        """Redimensionner en gardant le ratio"""
        h, w = image.shape[:2]
        ratio = min(max_width / w, max_height / h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def convert_to_rgb(image: np.ndarray) -> np.ndarray:
        """Convertir une image BGR en RGB"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    @staticmethod
    def convert_to_bgr(image: np.ndarray) -> np.ndarray:
        """Convertir une image RGB en BGR"""
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    @staticmethod
    def convert_to_gray(image: np.ndarray) -> np.ndarray:
        """Convertir en niveaux de gris"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def save_image(image: np.ndarray, path: str, quality: int = 95) -> bool:
        """
        Sauvegarder une image

        Args:
            image: Image à sauvegarder
            path: Chemin de destination
            quality: Qualité JPEG (0-100)

        Returns:
            True si succès
        """
        try:
            if path.lower().endswith('.jpg') or path.lower().endswith('.jpeg'):
                cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(path, image)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False

    @staticmethod
    def load_image(path: str) -> Optional[np.ndarray]:
        """
        Charger une image depuis un fichier

        Args:
            path: Chemin du fichier

        Returns:
            Image ou None si erreur
        """
        try:
            image = cv2.imread(path)
            if image is None:
                print(f"Impossible de charger l'image: {path}")
            return image
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
            return None

    @staticmethod
    def image_to_bytes(image: np.ndarray, format: str = '.jpg') -> Optional[bytes]:
        """
        Convertir une image en bytes pour stockage BD

        Args:
            image: Image à convertir
            format: Format de sortie ('.jpg', '.png')

        Returns:
            Bytes de l'image
        """
        try:
            is_success, buffer = cv2.imencode(format, image)
            if is_success:
                return buffer.tobytes()
            return None
        except Exception as e:
            print(f"Erreur conversion en bytes: {e}")
            return None

    @staticmethod
    def bytes_to_image(image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Convertir des bytes en image

        Args:
            image_bytes: Bytes de l'image

        Returns:
            Image numpy array
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Erreur conversion depuis bytes: {e}")
            return None

    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convertir une image PIL en OpenCV"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Convertir une image OpenCV en PIL"""
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

    @staticmethod
    def draw_rectangle(image: np.ndarray, top: int, right: int,
                       bottom: int, left: int,
                       color: Tuple[int, int, int] = (0, 255, 0),
                       thickness: int = 2) -> np.ndarray:
        """
        Dessiner un rectangle sur une image

        Args:
            image: Image
            top, right, bottom, left: Coordonnées du rectangle
            color: Couleur BGR
            thickness: Épaisseur du trait

        Returns:
            Image avec rectangle
        """
        cv2.rectangle(image, (left, top), (right, bottom), color, thickness)
        return image

    @staticmethod
    def draw_text(image: np.ndarray, text: str, x: int, y: int,
                  color: Tuple[int, int, int] = (0, 255, 0),
                  font_scale: float = 0.6, thickness: int = 2,
                  bg_color: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        """
        Écrire du texte sur une image

        Args:
            image: Image
            text: Texte à écrire
            x, y: Position
            color: Couleur du texte BGR
            font_scale: Taille de la police
            thickness: Épaisseur du texte
            bg_color: Couleur de fond (optionnel)

        Returns:
            Image avec texte
        """
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Ajouter un fond si spécifié
        if bg_color:
            (text_width, text_height), baseline = cv2.getTextSize(
                text, font, font_scale, thickness
            )
            cv2.rectangle(
                image,
                (x, y - text_height - baseline),
                (x + text_width, y + baseline),
                bg_color,
                -1
            )

        cv2.putText(image, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
        return image

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotation d'une image

        Args:
            image: Image à faire pivoter
            angle: Angle en degrés

        Returns:
            Image pivotée
        """
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (width, height))

    @staticmethod
    def flip_image(image: np.ndarray, flip_code: int = 1) -> np.ndarray:
        """
        Retourner une image

        Args:
            image: Image à retourner
            flip_code: 0 = vertical, 1 = horizontal, -1 = both

        Returns:
            Image retournée
        """
        return cv2.flip(image, flip_code)

    @staticmethod
    def crop_face(image: np.ndarray, top: int, right: int,
                  bottom: int, left: int, padding: int = 20) -> np.ndarray:
        """
        Extraire et rogner un visage avec padding

        Args:
            image: Image source
            top, right, bottom, left: Coordonnées du visage
            padding: Padding à ajouter

        Returns:
            Image du visage rogné
        """
        height, width = image.shape[:2]

        # Ajouter du padding
        top = max(0, top - padding)
        left = max(0, left - padding)
        bottom = min(height, bottom + padding)
        right = min(width, right + padding)

        return image[top:bottom, left:right]

    @staticmethod
    def enhance_brightness(image: np.ndarray, factor: float = 1.2) -> np.ndarray:
        """Améliorer la luminosité"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Appliquer un flou gaussien"""
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    @staticmethod
    def sharpen_image(image: np.ndarray) -> np.ndarray:
        """Accentuer les contours"""
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)