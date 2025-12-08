import sys
import os

# Configuration simple
class Config:
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "smart_home"
    DB_USER = "postgres"
    DB_PASSWORD = "your_password"  # À changer!
    ARDUINO_PORT = "COM3"  # Windows: COM3, Linux: /dev/ttyACM0

# Import des modules
try:
    from database import Database
    from face_manager import SimpleFaceRecognition
    from arduino_controller import ArduinoController
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Vérifiez que vous avez installé les dépendances:")
    print("pip install opencv-python numpy psycopg2-binary pyserial python-dotenv")
    sys.exit(1)

def main_menu():
    """Menu principal simplifié"""
    print("\n" + "=" * 40)
    print("   SMART HOME ACCESS - SIMPLIFIE")
    print("=" * 40)
    
    # Initialiser les composants
    try:
        db = Database()
        face_rec = SimpleFaceRecognition(db)
        arduino = ArduinoController(Config.ARDUINO_PORT)
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return
    
    while True:
        print("\nMENU PRINCIPAL:")
        print("1. Enregistrer un nouvel utilisateur")
        print("2. Mode surveillance (reconnaissance continue)")
        print("3. Lister les utilisateurs")
        print("4. Voir les logs d'accès")
        print("5. Tester Arduino")
        print("6. Quitter")
        
        choix = input("\nVotre choix (1-6): ").strip()
        
        if choix == "1":
            enregistrer_utilisateur(face_rec)
        elif choix == "2":
            face_rec.continuous_recognition(arduino)
        elif choix == "3":
            lister_utilisateurs(db)
        elif choix == "4":
            afficher_logs(db)
        elif choix == "5":
            tester_arduino(arduino)
        elif choix == "6":
            print("\n👋 Au revoir!")
            arduino.close()
            break
        else:
            print("❌ Choix invalide")

def enregistrer_utilisateur(face_rec):
    """Enregistre un nouvel utilisateur"""
    print("\n➕ ENREGISTREMENT UTILISATEUR")
    name = input("Nom complet: ").strip()
    username = input("Nom d'utilisateur: ").strip().lower()
    
    if not name or not username:
        print("❌ Nom et nom d'utilisateur requis")
        return
    
    print(f"\nPrêt à enregistrer {name}...")
    input("Appuyez sur Entrée pour démarrer la capture du visage")
    
    if face_rec.register_new_user(name, username):
        print(f"\n✅ {name} enregistré avec succès!")
    else:
        print(f"\n❌ Échec de l'enregistrement")

def lister_utilisateurs(db):
    """Affiche la liste des utilisateurs"""
    print("\n👥 LISTE DES UTILISATEURS")
    print("-" * 40)
    
    users = db.get_users()
    if not users:
        print("Aucun utilisateur enregistré")
        return
    
    for user_id, name, username, is_active in users:
        status = "✓ ACTIF" if is_active else "✗ INACTIF"
        print(f"{user_id:03d}. {name:<20} ({username}) - {status}")

def afficher_logs(db):
    """Affiche les logs récents"""
    print("\n📋 LOGS RECENTS")
    print("-" * 60)
    
    logs = db.get_recent_logs(limit=15)
    if not logs:
        print("Aucun log disponible")
        return
    
    for log_id, name, status, confidence, timestamp in logs:
        nom = name if name else "INCONNU"
        conf = f"{confidence:.1%}" if confidence else "N/A"
        date_str = timestamp.strftime("%H:%M") if timestamp else "N/A"
        
        if status == "GRANTED":
            status_display = "✅ AUTORISE"
        else:
            status_display = "❌ REFUSE"
        
        print(f"{date_str} - {nom:<15} - {status_display:<12} - {conf}")

def tester_arduino(arduino):
    """Teste les commandes Arduino"""
    print("\n🔧 TEST ARDUINO")
    print("1. Tester accès autorisé (LED verte)")
    print("2. Tester accès refusé (LED rouge)")
    print("3. Tester alarme")
    
    choix = input("\nChoix (1-3): ").strip()
    
    if choix == "1":
        arduino.grant_access()
        print("✅ LED verte allumée")
    elif choix == "2":
        arduino.deny_access()
        print("✅ LED rouge allumée")
    elif choix == "3":
        arduino.trigger_alarm()
        print("✅ Alarme déclenchée")
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Programme interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()