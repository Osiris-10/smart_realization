"""Lancer l'application web de reconnaissance faciale"""
import os
import sys

# Ajouter le dossier courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importer et lancer l'application
from web.app import run_app

if __name__ == '__main__':
    print("\n" + "="*60)
    print("   SYSTÈME DE RECONNAISSANCE FACIALE - VERSION WEB")
    print("="*60)
    print("\n   Démarrage du serveur...")
    print("   Une fois démarré, ouvrez: http://localhost:5000\n")
    
    run_app()
