"""Script de test pour Arduino"""
import time

try:
    import serial
    print("✅ pyserial installé")
except ImportError:
    print("❌ pyserial non installé! Exécutez: pip install pyserial")
    exit(1)

PORT = "COM5"
BAUD_RATE = 9600

print(f"\n🔌 Tentative de connexion à {PORT}...")
print("   (Assurez-vous que Arduino IDE est FERMÉ!)\n")

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=2)
    print(f"✅ Connecté à {PORT}")
    
    # Attendre que l'Arduino se réinitialise
    print("⏳ Attente de l'Arduino (2 secondes)...")
    time.sleep(2)
    
    # Test LED verte (accès autorisé)
    print("\n🟢 Test LED VERTE (accès autorisé)...")
    ser.write(b'G')
    ser.flush()
    print("   Commande 'G' envoyée!")
    time.sleep(4)
    
    # Test LED rouge (accès refusé)
    print("\n🔴 Test LED ROUGE (accès refusé)...")
    ser.write(b'R')
    ser.flush()
    print("   Commande 'R' envoyée!")
    time.sleep(4)
    
    # Éteindre tout
    print("\n⚫ Extinction des LEDs...")
    ser.write(b'O')
    ser.flush()
    
    ser.close()
    print("\n✅ Test terminé avec succès!")
    
except serial.SerialException as e:
    print(f"❌ Erreur: {e}")
    print("\n   Solutions possibles:")
    print("   1. Fermez Arduino IDE complètement")
    print("   2. Vérifiez que l'Arduino est sur COM5")
    print("   3. Débranchez et rebranchez l'Arduino")
except Exception as e:
    print(f"❌ Erreur inattendue: {e}")
