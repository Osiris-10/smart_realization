import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import time

class SimpleFaceRecognition:
    def __init__(self, database):
        self.db = database
        self.known_faces = []
        self.known_user_ids = []
        self.known_usernames = []
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        self.load_faces()
    
    def load_faces(self):
        """Charge les visages depuis la base de données"""
        # Pour simplifier, on va stocker des images de référence
        # et utiliser une méthode basique de comparaison
        print("📊 Chargement des visages...")
        
        # Créer dossier faces s'il n'existe pas
        os.makedirs("faces", exist_ok=True)
        
        # Lister les fichiers de visages
        face_files = [f for f in os.listdir("faces") if f.endswith('.jpg')]
        
        for face_file in face_files:
            username = face_file.split('_')[0]
            user_id = self.get_user_id_from_username(username)
            
            if user_id:
                img_path = os.path.join("faces", face_file)
                face_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                
                if face_img is not None:
                    # Redimensionner à une taille standard
                    face_img = cv2.resize(face_img, (100, 100))
                    self.known_faces.append(face_img)
                    self.known_user_ids.append(user_id)
                    self.known_usernames.append(username)
        
        print(f"✅ {len(self.known_faces)} visages chargés")
    
    def get_user_id_from_username(self, username):
        """Récupère l'ID utilisateur depuis la base"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = %s", 
                (username,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except:
            return None
    
    def detect_face(self, frame):
        """Détecte un visage dans l'image"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            return gray[y:y+h, x:x+w], (x, y, w, h)
        return None, None
    
    def extract_face_features(self, face_image):
        """Extrait des caractéristiques simples du visage"""
        # Redimensionner
        face_img = cv2.resize(face_image, (100, 100))
        
        # Appliquer un flou pour réduire le bruit
        face_img = cv2.GaussianBlur(face_img, (5, 5), 0)
        
        # Calculer l'histogramme (caractéristique simple)
        hist = cv2.calcHist([face_img], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist
    
    def compare_faces(self, face1_features, face2_features):
        """Compare deux visages avec une méthode simple"""
        # Utiliser la corrélation comme mesure de similarité
        correlation = cv2.compareHist(
            face1_features.astype(np.float32), 
            face2_features.astype(np.float32), 
            cv2.HISTCMP_CORREL
        )
        
        # Convertir en pourcentage de similarité (0-100%)
        similarity = (correlation + 1) / 2 * 100
        
        return similarity
    
    def recognize_face(self, frame):
        """Reconnaît un visage dans une image"""
        # Détecter le visage
        face_img, face_location = self.detect_face(frame)
        
        if face_img is None:
            return False, None, None, 0.0
        
        # Extraire les caractéristiques
        current_features = self.extract_face_features(face_img)
        
        best_match = None
        best_similarity = 0
        best_user_id = None
        best_username = None
        
        # Comparer avec tous les visages connus
        for i, known_face in enumerate(self.known_faces):
            known_features = self.extract_face_features(known_face)
            similarity = self.compare_faces(current_features, known_features)
            
            if similarity > best_similarity and similarity > 70:  # Seuil de 70%
                best_similarity = similarity
                best_match = i
        
        if best_match is not None:
            return (
                True,
                self.known_user_ids[best_match],
                self.known_usernames[best_match],
                best_similarity
            )
        
        return False, None, None, 0.0
    
    def capture_new_face(self, username):
        """Capture un nouveau visage pour l'enregistrement"""
        print(f"\n📸 Enregistrement de {username}")
        print("Regardez la caméra et appuyez sur ESPACE")
        
        video_capture = cv2.VideoCapture(0)
        face_images = []
        
        while len(face_images) < 5:  # Prendre 5 images
            ret, frame = video_capture.read()
            if not ret:
                continue
            
            # Détecter le visage
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Vérifier les yeux pour s'assurer que c'est un vrai visage
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (255, 0, 0), 2)
            
            # Afficher les instructions
            cv2.putText(frame, f"Capture {len(face_images)+1}/5", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "ESPACE: capturer | ESC: annuler", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow("Enregistrement Visage", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            
            elif key == 32:  # ESPACE
                if len(faces) > 0 and len(eyes) >= 1:  # Au moins un œil détecté
                    # Extraire le visage
                    face_img = gray[y:y+h, x:x+w]
                    face_img = cv2.resize(face_img, (100, 100))
                    face_images.append(face_img)
                    print(f"  ✓ Capture {len(face_images)} réussie")
                    
                    # Feedback visuel
                    frame[:] = (0, 255, 0)
                    cv2.imshow("Enregistrement Visage", frame)
                    cv2.waitKey(300)
                    time.sleep(0.5)  # Pause entre les captures
        
        video_capture.release()
        cv2.destroyAllWindows()
        
        if face_images:
            # Prendre la meilleure image (la plus nette)
            # Calculer la netteté (variance de Laplacian)
            sharpness_scores = []
            for img in face_images:
                laplacian = cv2.Laplacian(img, cv2.CV_64F)
                sharpness_scores.append(laplacian.var())
            
            best_idx = np.argmax(sharpness_scores)
            best_face = face_images[best_idx]
            
            # Sauvegarder l'image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"faces/{username}_{timestamp}.jpg"
            cv2.imwrite(filename, best_face)
            
            print(f"✅ Visage sauvegardé: {filename}")
            return best_face
        
        return None
    
    def register_new_user(self, name, username):
        """Enregistre un nouvel utilisateur"""
        # Vérifier si le nom d'utilisateur existe
        users = self.db.get_users()
        for user in users:
            if user[2] == username:  # username à l'index 2
                print(f"❌ Le nom d'utilisateur '{username}' existe déjà")
                return False
        
        # Ajouter l'utilisateur à la base
        user_id = self.db.add_user(name, username)
        if not user_id:
            return False
        
        # Capturer le visage
        face_img = self.capture_new_face(username)
        if face_img is None:
            print("❌ Échec de la capture du visage")
            return False
        
        # Recharger les visages
        self.load_faces()
        
        print(f"✅ Utilisateur {name} enregistré avec succès!")
        return True
    
    def continuous_recognition(self, arduino_controller):
        """Mode reconnaissance continue"""
        print("\n🎭 Mode reconnaissance active")
        print("Appuyez sur 'q' pour quitter")
        
        video_capture = cv2.VideoCapture(0)
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Reconnaître le visage
            recognized, user_id, username, confidence = self.recognize_face(frame)
            
            # Dessiner le résultat
            if recognized:
                color = (0, 255, 0)  # Vert
                status = f"ACCES AUTORISE: {username} ({confidence:.0f}%)"
                
                # Commander Arduino
                arduino_controller.grant_access()
                
                # Log dans la base
                self.db.log_access(
                    user_id, 
                    "GRANTED", 
                    confidence/100,  # Convertir en décimale
                    {"mode": "auto"}
                )
                
            else:
                color = (0, 0, 255)  # Rouge
                status = "ACCES REFUSE"
                
                # Commander Arduino
                arduino_controller.deny_access()
                
                # Log dans la base
                self.db.log_access(
                    None, 
                    "DENIED", 
                    None,
                    {"mode": "auto"}
                )
            
            # Afficher le statut
            cv2.putText(frame, status, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            cv2.imshow("Smart Home Access", frame)
            
            # Quitter avec 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        video_capture.release()
        cv2.destroyAllWindows()