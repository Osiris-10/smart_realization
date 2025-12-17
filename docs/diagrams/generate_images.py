"""
Script pour générer les images des diagrammes PlantUML

MÉTHODE 1: Utiliser le serveur PlantUML en ligne (recommandé - pas d'installation)
MÉTHODE 2: Installer PlantUML localement

Pour exécuter: python docs/diagrams/generate_images.py
"""

import os
import requests
import zlib
import base64

# Dossier des diagrammes
DIAGRAMS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(DIAGRAMS_DIR, "images")

# Créer le dossier de sortie
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Encodage PlantUML pour l'URL
def encode_plantuml(text):
    """Encode le texte PlantUML pour l'URL du serveur"""
    compressed = zlib.compress(text.encode('utf-8'))[2:-4]
    
    # Encodage base64 spécial PlantUML
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    result = ""
    
    for i in range(0, len(compressed), 3):
        if i + 2 < len(compressed):
            b1, b2, b3 = compressed[i], compressed[i+1], compressed[i+2]
        elif i + 1 < len(compressed):
            b1, b2, b3 = compressed[i], compressed[i+1], 0
        else:
            b1, b2, b3 = compressed[i], 0, 0
        
        result += alphabet[b1 >> 2]
        result += alphabet[((b1 & 0x3) << 4) | (b2 >> 4)]
        result += alphabet[((b2 & 0xF) << 2) | (b3 >> 6)]
        result += alphabet[b3 & 0x3F]
    
    return result


def generate_image_from_server(puml_file, output_format="png"):
    """Génère une image via le serveur PlantUML en ligne"""
    
    # Lire le fichier .puml
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    # Encoder pour l'URL
    encoded = encode_plantuml(puml_content)
    
    # URL du serveur PlantUML
    url = f"http://www.plantuml.com/plantuml/{output_format}/{encoded}"
    
    # Télécharger l'image
    response = requests.get(url)
    
    if response.status_code == 200:
        # Nom du fichier de sortie
        base_name = os.path.splitext(os.path.basename(puml_file))[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_name}.{output_format}")
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Généré: {output_file}")
        return output_file
    else:
        print(f"❌ Erreur pour {puml_file}: {response.status_code}")
        return None


def main():
    print("\n" + "="*60)
    print("   GÉNÉRATION DES DIAGRAMMES EN IMAGES")
    print("="*60 + "\n")
    
    # Trouver tous les fichiers .puml
    puml_files = [f for f in os.listdir(DIAGRAMS_DIR) if f.endswith('.puml')]
    
    if not puml_files:
        print("❌ Aucun fichier .puml trouvé!")
        return
    
    print(f"📁 Fichiers trouvés: {len(puml_files)}")
    print(f"📂 Dossier de sortie: {OUTPUT_DIR}\n")
    
    # Générer les images
    for puml_file in puml_files:
        full_path = os.path.join(DIAGRAMS_DIR, puml_file)
        print(f"🔄 Traitement: {puml_file}")
        generate_image_from_server(full_path, "png")
    
    print("\n" + "="*60)
    print("   TERMINÉ!")
    print("="*60)
    print(f"\n📂 Les images sont dans: {OUTPUT_DIR}")
    print("\nVous pouvez aussi utiliser ces outils en ligne:")
    print("  • https://www.plantuml.com/plantuml/uml/")
    print("  • https://plantuml-editor.kkeisuke.com/")
    print("  • VS Code extension: 'PlantUML'")


if __name__ == "__main__":
    main()
