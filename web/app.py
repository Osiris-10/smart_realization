"""Application Flask pour le système de reconnaissance faciale"""
from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for
from flask_cors import CORS
import cv2
import threading
import time
import sys
import os

# Ajouter le dossier parent au path pour importer les modules existants
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseConnection
from services.user_service import UserService
from services.profile_service import ProfileService
from services.access_service import AccessService
from services.arduino_service import signal_access_granted, signal_access_denied, init_arduino
from services.email_service import send_security_alert
from core.face_recognition import FaceRecognitionEngine
from core.authentication import AuthenticationManager
from utils.logger import Logger

logger = Logger()

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = 'votre_cle_secrete_ici_12345'
CORS(app)

# Variables globales
db = None
user_service = None
profile_service = None
access_service = None
face_engine = None
auth_manager = None
camera = None
camera_lock = threading.Lock()

# État de la reconnaissance
recognition_state = {
    'active': False,
    'last_result': None,
    'last_user': None,
    'attempts': 0,
    'last_attempt_time': 0  # Pour éviter les tentatives trop rapides
}


def init_services():
    """Initialiser tous les services"""
    global db, user_service, profile_service, access_service, face_engine, auth_manager
    
    try:
        logger.log_info("Initialisation des services web...")
        
        db = DatabaseConnection()
        db.connect()
        
        auth_manager = AuthenticationManager()
        user_service = UserService(db)
        profile_service = ProfileService(db)
        access_service = AccessService(db)
        face_engine = FaceRecognitionEngine()
        
        # Charger les profils faciaux
        profiles = profile_service.get_all_profiles()
        for profile in profiles:
            user = user_service.get_user_by_id(profile.personne_id)
            if user and profile.embedding:
                face_engine.load_profile(
                    profile.personne_id,
                    user.username,
                    profile.embedding,
                    user.password
                )
        
        # Initialiser Arduino
        arduino_ok = init_arduino()
        if arduino_ok:
            logger.log_info("Arduino initialisé avec succès")
            print("✅ Arduino initialisé et prêt pour les signaux")
        else:
            logger.log_warning("Arduino non connecté - les signaux seront ignorés")
            print("⚠️ Arduino non connecté - les signaux seront ignorés")
        
        logger.log_info("Services web initialisés avec succès")
        return True
    except Exception as e:
        logger.log_error(f"Erreur initialisation services: {e}")
        return False


def get_camera():
    """Obtenir l'instance de la caméra"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera


def generate_frames():
    """Générateur de frames pour le streaming vidéo - Utilise le même moteur que Tkinter"""
    global recognition_state
    
    while True:
        with camera_lock:
            cam = get_camera()
            success, frame = cam.read()
            
        if not success:
            break
        
        current_time = time.time()
        
        # Traitement de reconnaissance si actif
        if recognition_state['active']:
            # Utiliser le même moteur de détection que Tkinter (optimisé avec CLAHE, multi-tentatives)
            face_locations, face_encodings = face_engine.detect_faces(frame)
            
            if face_locations and len(face_locations) > 0:
                top, right, bottom, left = face_locations[0]
                
                if face_encodings and len(face_encodings) > 0:
                    # Reconnaissance avec le même moteur que Tkinter
                    personne_id, username, password, similarity = face_engine.recognize_face(face_encodings[0])
                    
                    if personne_id:
                        # RECONNU - Accorder l'accès automatiquement (comme Tkinter)
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)
                        cv2.putText(frame, f"RECONNU: {username}", (left, bottom + 25),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Accorder l'accès UNE SEULE FOIS
                        if recognition_state['last_result'] != 'granted':
                            recognition_state['last_result'] = 'granted'
                            recognition_state['last_user'] = {'id': personne_id, 'username': username, 'similarity': similarity}
                            recognition_state['attempts'] = 0
                            recognition_state['active'] = False  # Arrêter la reconnaissance
                            
                            # Logger l'accès et signal Arduino
                            logger.log_info(f"[WEB] Envoi signal Arduino GRANTED pour {username}")
                            print(f"🟢 [WEB] Envoi signal Arduino GRANTED pour {username}")
                            signal_access_granted()
                            access_service.log_access_attempt(personne_id, 'GRANTED', 'FACE_ONLY', similarity_score=similarity)
                            logger.log_info(f"Accès accordé automatiquement à {username}")
                    else:
                        # NON RECONNU - Afficher le cadre rouge
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 3)
                        cv2.putText(frame, f"INCONNU ({recognition_state['attempts']}/3)", (left, bottom + 25),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Incrémenter les tentatives avec un délai de 1.5 secondes entre chaque
                        if recognition_state['last_result'] != 'failed':
                            if current_time - recognition_state['last_attempt_time'] >= 1.5:
                                recognition_state['attempts'] += 1
                                recognition_state['last_attempt_time'] = current_time
                                logger.log_info(f"Tentative {recognition_state['attempts']}/3 - Visage non reconnu")
                                
                                # Après 3 tentatives, refuser l'accès automatiquement
                                if recognition_state['attempts'] >= 3:
                                    recognition_state['last_result'] = 'failed'
                                    recognition_state['active'] = False
                                    
                                    logger.log_info("[WEB] Envoi signal Arduino DENIED - 3 tentatives échouées")
                                    print("🔴 [WEB] Envoi signal Arduino DENIED - 3 tentatives échouées")
                                    signal_access_denied()
                                    access_service.log_access_attempt(None, 'DENIED', 'FACE_ONLY')
                                    threading.Thread(target=send_security_alert, args=(None, "Visage non reconnu (3 tentatives) - Web"), daemon=True).start()
                                    logger.log_warning("Accès refusé automatiquement - 3 tentatives échouées")
                else:
                    # Visage détecté mais pas d'encodage
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                    cv2.putText(frame, "Analyse...", (left, bottom + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                cv2.putText(frame, "Positionnez votre visage", (20, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Encoder en JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.03)  # ~30 FPS


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/user')
def user_mode():
    """Mode utilisateur - Reconnaissance faciale"""
    return render_template('user.html')


@app.route('/admin')
def admin_login():
    """Page de connexion admin"""
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard admin"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')


@app.route('/video_feed')
def video_feed():
    """Flux vidéo de la caméra"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


# ==================== API ====================

@app.route('/api/recognition/start', methods=['POST'])
def start_recognition():
    """Démarrer la reconnaissance"""
    recognition_state['active'] = True
    recognition_state['last_result'] = None
    recognition_state['last_user'] = None
    recognition_state['attempts'] = 0
    recognition_state['last_attempt_time'] = 0
    return jsonify({'status': 'started'})


@app.route('/api/recognition/stop', methods=['POST'])
def stop_recognition():
    """Arrêter la reconnaissance"""
    recognition_state['active'] = False
    return jsonify({'status': 'stopped'})


@app.route('/api/recognition/status')
def recognition_status():
    """État de la reconnaissance"""
    return jsonify(recognition_state)


@app.route('/api/recognition/grant_access', methods=['POST'])
def grant_access():
    """Accorder l'accès manuellement (si pas fait automatiquement)"""
    user = recognition_state.get('last_user')
    if user:
        # Vérifier si pas déjà loggé
        if recognition_state.get('last_result') != 'granted':
            signal_access_granted()
            access_service.log_access_attempt(user['id'], 'GRANTED', 'FACE_ONLY', similarity_score=user['similarity'])
            recognition_state['last_result'] = 'granted'
        recognition_state['active'] = False
        return jsonify({'status': 'granted', 'user': user})
    return jsonify({'status': 'error', 'message': 'No user recognized'})


@app.route('/api/recognition/deny_access', methods=['POST'])
def deny_access():
    """Refuser l'accès manuellement (si pas fait automatiquement)"""
    # Vérifier si pas déjà loggé
    if recognition_state.get('last_result') != 'failed':
        signal_access_denied()
        access_service.log_access_attempt(None, 'DENIED', 'FACE_ONLY')
        threading.Thread(target=send_security_alert, args=(None, "Accès refusé - Web"), daemon=True).start()
        recognition_state['last_result'] = 'failed'
    recognition_state['active'] = False
    return jsonify({'status': 'denied'})


@app.route('/api/recognition/verify_pin', methods=['POST'])
def verify_pin():
    """Vérifier le mot de passe après échec reconnaissance"""
    data = request.json
    password = data.get('password', '')
    
    # Chercher un utilisateur avec ce mot de passe
    users = user_service.get_all_active_users()
    for user in users:
        if auth_manager.verify_password(password, user.password):
            logger.log_info(f"[WEB] PIN correct - Envoi signal Arduino GRANTED pour {user.username}")
            print(f"🟢 [WEB] PIN correct - Envoi signal Arduino GRANTED pour {user.username}")
            signal_access_granted()
            access_service.log_access_attempt(user.personne_id, 'GRANTED', 'PIN_ONLY')
            return jsonify({'status': 'granted', 'username': user.username})
    
    # Mot de passe incorrect
    logger.log_info("[WEB] PIN incorrect - Envoi signal Arduino DENIED")
    print("🔴 [WEB] PIN incorrect - Envoi signal Arduino DENIED")
    signal_access_denied()
    access_service.log_access_attempt(None, 'DENIED', 'PIN_ONLY')
    threading.Thread(target=send_security_alert, args=(None, "PIN incorrect - Web"), daemon=True).start()
    return jsonify({'status': 'denied'})


@app.route('/api/auth/admin_login', methods=['POST'])
def api_admin_login():
    """Connexion admin"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = user_service.get_user_by_username(username)
    if user and user.role == 'ADMIN':
        if auth_manager.verify_password(password, user.password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Identifiants incorrects'})


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Déconnexion"""
    session.clear()
    return jsonify({'status': 'success'})


@app.route('/api/users')
def api_get_users():
    """Liste des utilisateurs - utilise les mêmes services que Tkinter"""
    try:
        # Utiliser le service comme Tkinter
        users = user_service.get_all_users()
        profiles = profile_service.get_all_profiles()
        
        # IDs des utilisateurs avec profil facial
        profile_ids = {p.personne_id for p in profiles}
        
        result = []
        for u in users:
            result.append({
                'id': u.personne_id,
                'username': u.username,
                'email': u.email,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': str(u.created_at) if u.created_at else None,
                'has_profile': u.personne_id in profile_ids
            })
        return jsonify(result)
    except Exception as e:
        logger.log_error(f"Erreur API users: {e}")
        import traceback
        logger.log_error(traceback.format_exc())
        return jsonify([])


@app.route('/api/users/<int:user_id>')
def api_get_user(user_id):
    """Détails d'un utilisateur"""
    user = user_service.get_user_by_id(user_id)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/users/extract_embeddings', methods=['POST'])
def api_extract_embeddings():
    """Extraire les embeddings d'une image capturée - Même méthode que Tkinter"""
    try:
        import face_recognition as fr
        import base64
        import numpy as np
        import tempfile
        import os
        
        data = request.json
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'status': 'error', 'message': 'Aucune image fournie'})
        
        # Décoder l'image base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # MÉTHODE 1: Sauvegarder temporairement et utiliser load_image_file (comme Tkinter)
        temp_file = None
        try:
            # Créer un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_file.write(image_bytes)
            temp_file.close()
            
            logger.log_info(f"Image temporaire créée: {temp_file.name}")
            
            # Charger l'image avec face_recognition (comme Tkinter)
            image = fr.load_image_file(temp_file.name)
            
            if image is None:
                return jsonify({'status': 'error', 'message': 'Image invalide - impossible de charger'})
            
            logger.log_info(f"Image chargée: {image.shape}")
            
            # Détecter les visages avec le modèle HOG (par défaut, comme Tkinter)
            face_locations = fr.face_locations(image, model='hog')
            
            logger.log_info(f"Visages détectés (HOG): {len(face_locations)}")
            
            # Si aucun visage avec HOG, essayer avec CNN (plus précis mais plus lent)
            if len(face_locations) == 0:
                logger.log_info("Tentative avec modèle CNN...")
                face_locations = fr.face_locations(image, model='cnn')
                logger.log_info(f"Visages détectés (CNN): {len(face_locations)}")
            
            if len(face_locations) == 0:
                return jsonify({'status': 'error', 'message': 'Aucun visage détecté. Assurez-vous que le visage est bien visible et éclairé.'})
            
            if len(face_locations) > 1:
                return jsonify({'status': 'error', 'message': f'{len(face_locations)} visages détectés. Utilisez une image avec un seul visage.'})
            
            # Extraire les embeddings (comme Tkinter)
            encodings = fr.face_encodings(image, face_locations)
            
            if not encodings or len(encodings) == 0:
                return jsonify({'status': 'error', 'message': 'Impossible d\'extraire les caractéristiques faciales'})
            
            embeddings = encodings[0].tolist()
            logger.log_info(f"Embeddings extraits avec succès: {len(embeddings)} caractéristiques")
            
            return jsonify({
                'status': 'success',
                'embeddings': embeddings,
                'count': len(embeddings)
            })
            
        finally:
            # Supprimer le fichier temporaire
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                logger.log_info("Fichier temporaire supprimé")
        
    except Exception as e:
        logger.log_error(f"Erreur extraction embeddings: {e}")
        import traceback
        logger.log_error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/users', methods=['POST'])
def api_create_user():
    """Créer un utilisateur avec profil facial obligatoire"""
    try:
        import numpy as np
        import base64
        import os
        
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'USER')
        embeddings = data.get('embeddings')
        image_data = data.get('image_data')
        
        # Validation
        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Username et password obligatoires'}), 400
        
        if not embeddings:
            return jsonify({'status': 'error', 'message': 'Les embeddings faciaux sont obligatoires'}), 400
        
        # Créer l'utilisateur
        user_id = user_service.create_user(
            username=username,
            password=password,
            email=email,
            role=role
        )
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Erreur création utilisateur'}), 400
        
        # Sauvegarder l'image si fournie
        image_url = None
        if image_data:
            try:
                uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image_filename = f"user_{user_id}.jpg"
                image_path = os.path.join(uploads_dir, image_filename)
                
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                
                image_url = image_filename
                logger.log_info(f"Image sauvegardée: {image_path}")
            except Exception as e:
                logger.log_warning(f"Erreur sauvegarde image: {e}")
        
        # Créer le profil facial
        embeddings_array = np.array(embeddings)
        profile_id = profile_service.create_profile(
            personne_id=user_id,
            embedding=embeddings_array,
            image_url=image_url
        )
        
        if not profile_id:
            # Supprimer l'utilisateur si le profil n'a pas pu être créé
            user_service.delete_user(user_id)
            return jsonify({'status': 'error', 'message': 'Erreur création profil facial'}), 400
        
        # Charger le profil dans le moteur de reconnaissance
        user = user_service.get_user_by_id(user_id)
        if user:
            face_engine.load_profile(user_id, username, embeddings_array, user.password)
        
        logger.log_info(f"Utilisateur {username} créé avec profil facial (ID: {user_id})")
        return jsonify({'status': 'success', 'id': user_id, 'profile_id': profile_id})
        
    except Exception as e:
        logger.log_error(f"Erreur création utilisateur: {e}")
        import traceback
        logger.log_error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    """Modifier un utilisateur"""
    data = request.json
    success = user_service.update_user(user_id, **data)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """Supprimer un utilisateur"""
    success = user_service.delete_user(user_id)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400


@app.route('/api/logs')
def api_get_logs():
    """Liste des logs d'accès - utilise les mêmes services que Tkinter"""
    try:
        # Utiliser le service comme Tkinter
        logs = access_service.get_all_access_logs(limit=100)
        
        result = []
        for log in logs:
            # Récupérer le username
            username = 'Inconnu'
            if log.personne_id:
                user = user_service.get_user_by_id(log.personne_id)
                if user:
                    username = user.username
            
            result.append({
                'id': log.access_id,
                'personne_id': log.personne_id,
                'access_result': log.access_result if log.access_result else '-',
                'access_method': log.access_method if log.access_method else '-',
                'similarity_score': float(log.similarity_score) if log.similarity_score else None,
                'access_time': str(log.horaire) if log.horaire else None,
                'username': username
            })
        return jsonify(result)
    except Exception as e:
        logger.log_error(f"Erreur API logs: {e}")
        import traceback
        logger.log_error(traceback.format_exc())
        return jsonify([])


@app.route('/api/stats')
def api_get_stats():
    """Statistiques - utilise les mêmes services que Tkinter"""
    try:
        # Utiliser les services comme Tkinter
        users = user_service.get_all_users()
        profiles = profile_service.get_all_profiles()
        logs = access_service.get_all_access_logs(limit=1000)
        
        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active)
        total_profiles = len(profiles)
        total_access = len(logs)
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'total_profiles': total_profiles,
            'total_access': total_access
        })
    except Exception as e:
        logger.log_error(f"Erreur API stats: {e}")
        import traceback
        logger.log_error(traceback.format_exc())
        return jsonify({
            'total_users': 0,
            'active_users': 0,
            'total_profiles': 0,
            'total_access': 0
        })


def run_app():
    """Lancer l'application"""
    if init_services():
        print("\n" + "="*50)
        print("   SERVEUR WEB DÉMARRÉ")
        print("="*50)
        print("   Ouvrez votre navigateur à:")
        print("   http://localhost:5000")
        print("="*50 + "\n")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    else:
        print("Erreur: Impossible d'initialiser les services")


if __name__ == '__main__':
    run_app()
