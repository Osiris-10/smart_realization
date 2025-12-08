import psycopg2
import pickle
import numpy as np
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.config = Config()
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connexion à PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            print("✅ Connecté à PostgreSQL")
        except Exception as e:
            print(f"❌ Erreur connexion PostgreSQL: {e}")
            self.conn = None
    
    def create_tables(self):
        """Création des tables si elles n'existent pas"""
        if not self.conn:
            return
        
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS face_encodings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                encoding BYTEA NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS access_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                status VARCHAR(20) NOT NULL,
                confidence FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS admin_user (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            )
            """
        ]
        
        try:
            cursor = self.conn.cursor()
            for query in queries:
                cursor.execute(query)
            self.conn.commit()
            cursor.close()
            print("✅ Tables créées avec succès")
            
            # Créer l'utilisateur admin par défaut
            self.create_admin_user()
            
        except Exception as e:
            print(f"❌ Erreur création tables: {e}")
    
    def create_admin_user(self):
        """Crée l'utilisateur admin par défaut"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM admin_user")
            count = cursor.fetchone()[0]
            
            if count == 0:
                import hashlib
                password_hash = hashlib.sha256(
                    self.config.ADMIN_PASSWORD.encode()
                ).hexdigest()
                
                cursor.execute(
                    "INSERT INTO admin_user (username, password) VALUES (%s, %s)",
                    (self.config.ADMIN_USERNAME, password_hash)
                )
                self.conn.commit()
                print("✅ Utilisateur admin créé")
            
            cursor.close()
        except Exception as e:
            print(f"❌ Erreur création admin: {e}")
    
    def add_user(self, name, username):
        """Ajoute un nouvel utilisateur"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, username) VALUES (%s, %s) RETURNING id",
                (name, username)
            )
            user_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            print(f"✅ Utilisateur {name} ajouté (ID: {user_id})")
            return user_id
        except Exception as e:
            print(f"❌ Erreur ajout utilisateur: {e}")
            return None
    
    def save_face_encoding(self, user_id, encoding):
        """Enregistre l'encodage facial d'un utilisateur"""
        try:
            # Convertir numpy array en bytes
            encoding_bytes = pickle.dumps(encoding)
            
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO face_encodings (user_id, encoding) VALUES (%s, %s)",
                (user_id, psycopg2.Binary(encoding_bytes))
            )
            self.conn.commit()
            cursor.close()
            print(f"✅ Encodage facial sauvegardé pour l'utilisateur {user_id}")
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde encodage: {e}")
            return False
    
    def get_all_encodings(self):
        """Récupère tous les encodages faciaux"""
        encodings = []
        user_ids = []
        usernames = []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT fe.encoding, fe.user_id, u.username
                FROM face_encodings fe
                JOIN users u ON fe.user_id = u.id
                WHERE u.is_active = TRUE
            """)
            
            for encoding_bytes, user_id, username in cursor.fetchall():
                # Convertir bytes en numpy array
                encoding = pickle.loads(encoding_bytes)
                encodings.append(encoding)
                user_ids.append(user_id)
                usernames.append(username)
            
            cursor.close()
            print(f"✅ {len(encodings)} encodages chargés")
            
        except Exception as e:
            print(f"❌ Erreur chargement encodages: {e}")
        
        return encodings, user_ids, usernames
    
    def log_access(self, user_id, status, confidence=None, details=None):
        """Enregistre une tentative d'accès"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO access_logs (user_id, status, confidence, details)
                VALUES (%s, %s, %s, %s)
            """, (user_id, status, confidence, json.dumps(details) if details else None))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Erreur log accès: {e}")
            return False
    
    def get_users(self):
        """Liste tous les utilisateurs"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, username, is_active FROM users ORDER BY name")
            users = cursor.fetchall()
            cursor.close()
            return users
        except Exception as e:
            print(f"❌ Erreur récupération utilisateurs: {e}")
            return []
    
    def delete_user(self, user_id):
        """Supprime un utilisateur"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            self.conn.commit()
            cursor.close()
            print(f"✅ Utilisateur {user_id} supprimé")
            return True
        except Exception as e:
            print(f"❌ Erreur suppression utilisateur: {e}")
            return False
    
    def get_recent_logs(self, limit=50):
        """Récupère les logs récents"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT l.id, u.name, l.status, l.confidence, l.timestamp
                FROM access_logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.timestamp DESC
                LIMIT %s
            """, (limit,))
            logs = cursor.fetchall()
            cursor.close()
            return logs
        except Exception as e:
            print(f"❌ Erreur récupération logs: {e}")
            return []