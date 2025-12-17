# Diagrammes UML - Système de Reconnaissance Faciale (Web)

## 📁 Fichiers disponibles

| Fichier | Description |
|---------|-------------|
| `architecture.puml` | Architecture en couches du système |
| `use_case.puml` | Diagramme de cas d'utilisation |
| `sequence_reconnaissance.puml` | Séquence: Authentification par reconnaissance faciale |
| `sequence_pin.puml` | Séquence: Authentification par PIN (fallback) |
| `sequence_admin.puml` | Séquence: Création d'un utilisateur (admin) |

## 🖼️ Générer les images

### Méthode 1: Script Python (automatique)

```bash
# Installer requests si nécessaire
pip install requests

# Exécuter le script
python docs/diagrams/generate_images.py
```

Les images PNG seront générées dans `docs/diagrams/images/`

### Méthode 2: En ligne (manuel)

1. Ouvrir https://www.plantuml.com/plantuml/uml/
2. Copier-coller le contenu d'un fichier `.puml`
3. Cliquer sur "Submit" pour voir le diagramme
4. Clic droit → "Enregistrer l'image sous..."

### Méthode 3: VS Code Extension

1. Installer l'extension "PlantUML" dans VS Code
2. Ouvrir un fichier `.puml`
3. `Alt + D` pour prévisualiser
4. `Ctrl + Shift + P` → "PlantUML: Export Current Diagram"

### Méthode 4: Installation locale PlantUML

```bash
# Windows (avec Chocolatey)
choco install plantuml

# Ou télécharger plantuml.jar depuis:
# https://plantuml.com/download

# Générer une image
java -jar plantuml.jar architecture.puml
```

## 📊 Aperçu des diagrammes

### Architecture
```
┌─────────────────────────────────────┐
│     COUCHE PRÉSENTATION (HTML)      │
├─────────────────────────────────────┤
│     COUCHE API (Flask/app.py)       │
├─────────────────────────────────────┤
│     COUCHE SERVICES                 │
├─────────────────────────────────────┤
│     COUCHE CORE (Face Recognition)  │
├─────────────────────────────────────┤
│     COUCHE DONNÉES (PostgreSQL)     │
├─────────────────────────────────────┤
│     COUCHE MATÉRIELLE (Arduino)     │
└─────────────────────────────────────┘
```

### Cas d'utilisation
- **Utilisateur**: S'authentifier (visage ou PIN)
- **Admin**: Gérer utilisateurs, consulter logs, voir stats
- **Système**: Signaux Arduino, alertes email

### Séquences
- Reconnaissance faciale complète avec Arduino et logs
- Fallback PIN après 3 échecs
- Création utilisateur avec capture photo et embeddings
