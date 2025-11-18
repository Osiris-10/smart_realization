"""Paramètres généraux de l'application"""

# ===== RECONNAISSANCE FACIALE =====
FACE_RECOGNITION_TOLERANCE = 0.6
FACE_DETECTION_MODEL = 'hog'  # 'hog' (rapide) ou 'cnn' (précis)
MIN_FACE_SIZE = (50, 50)
SIMILARITY_THRESHOLD = 0.6

# ===== SÉCURITÉ =====
MAX_FAILED_FACE_ATTEMPTS = 3
MAX_FAILED_PIN_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # secondes (5 minutes)
PASSWORD_LENGTH = 6
PASSWORD_HASH_ALGORITHM = 'sha256'

# ===== ANTI-SPOOFING =====
ENABLE_ANTISPOOFING = True
BLINK_DETECTION_ENABLED = True
HEAD_TURN_DETECTION_ENABLED = True
ANTISPOOFING_THRESHOLD = 0.7
LIVENESS_CHECK_TIMEOUT = 5  # secondes

# ===== CAMÉRA =====
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30
CAMERA_FLIP = True  # Inverser horizontalement

# ===== INTERFACE UTILISATEUR =====
UI_THEME = 'light'
LANGUAGE = 'fr'
WINDOW_TITLE = "Système de Reconnaissance Faciale"
WINDOW_SIZE = (1200, 700)
FONT_FAMILY = 'Arial'
FONT_SIZE = 12

# ===== COULEURS =====
COLOR_SUCCESS = '#00FF00'
COLOR_ERROR = '#FF0000'
COLOR_WARNING = '#FFA500'
COLOR_INFO = '#0000FF'
COLOR_BG = '#FFFFFF'

# ===== LOGGING =====
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/app.log'
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ===== CHEMINS =====
ASSETS_DIR = 'assets'
IMAGES_DIR = 'assets/images'
SOUNDS_DIR = 'assets/sounds'
TEMP_DIR = 'temp'
UPLOADS_DIR = 'uploads'

# ===== TIMEOUTS =====
RECOGNITION_TIMEOUT = 10  # secondes
AUTH_DIALOG_TIMEOUT = 30  # secondes
CAMERA_INIT_TIMEOUT = 5  # secondes

# ===== SONS =====
SOUND_SUCCESS = 'success.wav'
SOUND_ERROR = 'error.wav'
SOUND_WARNING = 'warning.wav'


