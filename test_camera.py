# test_manual.py - Crée ce fichier à la racine
import face_recognition
import cv2

# Charger l'image sauvegardée
img = cv2.imread("debug_frames/test_frame.jpg")
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

print(f"Image shape: {rgb.shape}")

# Test HOG
print("\n=== TEST HOG ===")
faces_hog = face_recognition.face_locations(rgb, model='hog')
print(f"HOG: {len(faces_hog)} visages")
print(f"Positions: {faces_hog}")

# Test CNN
print("\n=== TEST CNN ===")
faces_cnn = face_recognition.face_locations(rgb, model='cnn')
print(f"CNN: {len(faces_cnn)} visages")
print(f"Positions: {faces_cnn}")

# Dessiner
for (top, right, bottom, left) in faces_hog:
    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

cv2.imwrite("debug_frames/resultat.jpg", img)
print("\n✅ Résultat sauvegardé: debug_frames/resultat.jpg")