"""Service de communication avec Arduino pour le contrôle d'accès"""
import time
import threading
from utils.logger import Logger

logger = Logger()

# Configuration Arduino
ARDUINO_PORT = "COM5"
BAUD_RATE = 9600
TIMEOUT = 2

# Vérifier si pyserial est installé
try:
    import serial
    SERIAL_AVAILABLE = True
    print("✅ pyserial est installé")
except ImportError:
    SERIAL_AVAILABLE = False
    print("❌ pyserial n'est pas installé! Exécutez: pip install pyserial")


class ArduinoService:
    """Service pour communiquer avec l'Arduino"""

    def __init__(self, port=ARDUINO_PORT, baud_rate=BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.is_connected = False
        
        if SERIAL_AVAILABLE:
            self.connect()
        else:
            print("❌ Arduino désactivé - pyserial non installé")

    def connect(self) -> bool:
        """Établir la connexion avec l'Arduino"""
        if not SERIAL_AVAILABLE:
            return False
            
        try:
            print(f"🔌 Tentative de connexion à Arduino sur {self.port}...")
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=TIMEOUT
            )
            # Attendre que l'Arduino se réinitialise après connexion série
            time.sleep(2)
            self.is_connected = True
            logger.log_info(f"Arduino connecté sur {self.port}")
            print(f"✅ Arduino connecté sur {self.port}")
            return True
        except serial.SerialException as e:
            logger.log_error(f"Erreur connexion Arduino: {e}")
            print(f"❌ Erreur connexion Arduino sur {self.port}: {e}")
            print("   Vérifiez que:")
            print("   1. L'Arduino est branché sur COM5")
            print("   2. Le moniteur série Arduino IDE est FERMÉ")
            print("   3. Aucun autre programme n'utilise COM5")
            self.is_connected = False
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Fermer la connexion"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.is_connected = False
            logger.log_info("Arduino déconnecté")
            print("🔌 Arduino déconnecté")

    def send_command(self, command: str) -> bool:
        """Envoyer une commande à l'Arduino"""
        try:
            if not self.is_connected:
                print("⚠️ Arduino non connecté, tentative de reconnexion...")
                if not self.connect():
                    return False
            
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(command.encode())
                self.serial_connection.flush()  # S'assurer que les données sont envoyées
                logger.log_info(f"Commande envoyée à Arduino: {command}")
                print(f"📡 Commande envoyée à Arduino: '{command}'")
                return True
            else:
                print("❌ Connexion série non ouverte")
                return False
        except Exception as e:
            logger.log_error(f"Erreur envoi commande Arduino: {e}")
            print(f"❌ Erreur envoi commande: {e}")
            self.is_connected = False
            return False

    def access_granted(self):
        """Signal d'accès autorisé - LED verte + buzzer"""
        print("🟢 Signal ACCÈS AUTORISÉ envoyé à Arduino")
        self.send_command('G')

    def access_denied(self):
        """Signal d'accès refusé - LED rouge + buzzer"""
        print("🔴 Signal ACCÈS REFUSÉ envoyé à Arduino")
        self.send_command('R')

    def reset(self):
        """Réinitialiser les LEDs"""
        self.send_command('O')


# Instance globale
arduino = None


def init_arduino():
    """Initialiser la connexion Arduino"""
    global arduino
    try:
        print("\n" + "="*50)
        print("   INITIALISATION ARDUINO")
        print("="*50)
        arduino = ArduinoService()
        if arduino.is_connected:
            print("✅ Arduino prêt!")
        else:
            print("⚠️ Arduino non connecté - les signaux seront ignorés")
        print("="*50 + "\n")
        return arduino.is_connected
    except Exception as e:
        logger.log_error(f"Impossible d'initialiser Arduino: {e}")
        print(f"❌ Erreur initialisation Arduino: {e}")
        return False


def signal_access_granted():
    """Envoyer signal accès autorisé"""
    global arduino
    print(">>> signal_access_granted() appelé")
    logger.log_info(">>> signal_access_granted() appelé")
    try:
        if arduino is None:
            print(">>> Arduino est None, initialisation...")
            init_arduino()
        if arduino and arduino.is_connected:
            print(f">>> Arduino connecté, envoi commande G...")
            # Exécuter directement (pas dans un thread) pour debug
            arduino.access_granted()
        else:
            print("⚠️ Arduino non connecté - signal ignoré")
            logger.log_warning("Arduino non connecté - signal GRANTED ignoré")
    except Exception as e:
        logger.log_error(f"Erreur signal Arduino: {e}")
        print(f"❌ Erreur: {e}")


def signal_access_denied():
    """Envoyer signal accès refusé"""
    global arduino
    print(">>> signal_access_denied() appelé")
    logger.log_info(">>> signal_access_denied() appelé")
    try:
        if arduino is None:
            print(">>> Arduino est None, initialisation...")
            init_arduino()
        if arduino and arduino.is_connected:
            print(f">>> Arduino connecté, envoi commande R...")
            # Exécuter directement (pas dans un thread) pour debug
            arduino.access_denied()
        else:
            print("⚠️ Arduino non connecté - signal ignoré")
            logger.log_warning("Arduino non connecté - signal DENIED ignoré")
    except Exception as e:
        logger.log_error(f"Erreur signal Arduino: {e}")
        print(f"❌ Erreur: {e}")
