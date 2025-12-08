import serial

# Ouvrir le port série (ajuster le port COM selon votre configuration)
arduino = serial.Serial('COM3', 9600, timeout=1)

def envoyer_commande(commande):
    arduino.write(commande.encode())

# Exemple après reconnaissance :
if visage_reconnu and acces_autorise:
    envoyer_commande('A')
elif visage_reconnu and acces_refuse:
    envoyer_commande('R')
elif tentative_spoofing:
    envoyer_commande('A')