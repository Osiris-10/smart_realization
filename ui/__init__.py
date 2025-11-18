"""Package UI - Interface utilisateur"""
from .main_window import MainWindow
from .camera_widget import CameraWidget
from .auth_dialog import AuthDialog
from .registration_window import RegistrationWindow
from ui.admin.admin_login_dialog import AdminLoginDialog  # AJOUTER
from ui.admin.admin_dashboard import AdminDashboard  # AJOUTER

__all__ = [
    'MainWindow',
    'CameraWidget',
    'AuthDialog',
    'RegistrationWindow',
    'AdminLoginDialog',
    'AdminDashboard'
]
