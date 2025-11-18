



"""Configuration de la base de données PostgreSQL"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),  # Port PostgreSQL par défaut
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'faces'),
    'options': '-c client_encoding=UTF8'  # Encodage UTF-8
}