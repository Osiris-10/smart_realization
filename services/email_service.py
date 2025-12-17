"""Service d'envoi d'emails pour les alertes de sécurité"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import os
from utils.logger import Logger

logger = Logger()

# Configuration email (Gmail)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# IMPORTANT: Utiliser un "App Password" Gmail, pas le mot de passe normal
# Pour créer un App Password: Google Account > Security > 2-Step Verification > App passwords
# Exemple: Si ton email est jordanmeira13@gmail.com, mets-le ici
# Et génère un App Password sur https://myaccount.google.com/apppasswords
SENDER_EMAIL = "jordanmeira13@gmail.com"  # Email qui ENVOIE les alertes
SENDER_PASSWORD = "hpsy bvvl ywfe rvtu"   # Remplace par ton App Password Gmail (16 caractères)
ALERT_RECIPIENT = "jordanmeira13@gmail.com"  # Email qui REÇOIT les alertes


class EmailService:
    """Service pour envoyer des emails d'alerte"""

    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.sender_email = SENDER_EMAIL
        self.sender_password = SENDER_PASSWORD
        self.recipient = ALERT_RECIPIENT
        logger.log_info("Service email initialisé")

    def send_denied_access_alert(self, image_path: str = None, reason: str = "Visage non reconnu") -> bool:
        """
        Envoyer une alerte par email lors d'un accès refusé
        
        Args:
            image_path: Chemin de l'image capturée (optionnel)
            reason: Raison du refus
            
        Returns:
            True si l'email a été envoyé avec succès
        """
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient
            msg['Subject'] = f"🚨 ALERTE SÉCURITÉ - Accès Refusé - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

            # Corps du message
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #e74c3c; color: white; padding: 15px; border-radius: 5px;">
                    <h2>🚨 ALERTE DE SÉCURITÉ</h2>
                </div>
                
                <div style="padding: 20px; background-color: #f9f9f9; margin-top: 10px; border-radius: 5px;">
                    <h3>Tentative d'accès non autorisée détectée</h3>
                    
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Date:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{datetime.now().strftime('%d/%m/%Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Heure:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{datetime.now().strftime('%H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Raison:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{reason}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Image capturée:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{'Oui (voir pièce jointe)' if image_path else 'Non disponible'}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 5px;">
                    <p><strong>⚠️ Action recommandée:</strong> Vérifiez les logs d'accès et l'image capturée pour identifier la personne.</p>
                </div>
                
                <hr style="margin-top: 30px;">
                <p style="color: #888; font-size: 12px;">
                    Ce message a été envoyé automatiquement par le système de reconnaissance faciale.
                </p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            # Joindre l'image si disponible
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                    msg.attach(img)

            # Envoyer l'email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.log_info(f"Email d'alerte envoyé à {self.recipient}")
            print(f"📧 Email d'alerte envoyé à {self.recipient}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.log_error("Erreur d'authentification SMTP - Vérifiez l'email et le mot de passe d'application")
            print("❌ Erreur: Authentification email échouée. Configurez un App Password Gmail.")
            return False
        except Exception as e:
            logger.log_error(f"Erreur envoi email: {e}")
            print(f"❌ Erreur envoi email: {e}")
            return False


# Instance globale pour faciliter l'utilisation
email_service = EmailService()


def send_security_alert(image_path: str = None, reason: str = "Visage non reconnu") -> bool:
    """Fonction helper pour envoyer une alerte"""
    return email_service.send_denied_access_alert(image_path, reason)
