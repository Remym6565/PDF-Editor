# PDF Editor Pro

Un éditeur PDF desktop moderne avec interface graphique, développé en Python avec PyQt6.

## Fonctionnalités

- **Ouverture, création et enregistrement** de fichiers PDF
- **Édition de texte** : ajout de texte avec choix de police, taille, gras, italique et couleur
- **Insertion d'images** : ajoutez des images directement sur vos pages PDF
- **Signature** : dessinez, importez ou réutilisez une signature enregistrée
- **Gestionnaire de pages** : réorganisez, fusionnez et divisez les pages
- **Mode édition** : affiche les blocs de texte et images existants pour modification
- **Annulation** (Undo) des dernières actions
- **Zoom** avant/arrière et ajustement à la hauteur de l'écran
- **Thème sombre** moderne

## Prérequis

- Python 3.8+
- PyQt6
- PyMuPDF (fitz)
- pypdf

## Installation

```bash
pip install PyQt6 PyMuPDF pypdf
```

## Utilisation

```bash
python main.py
```

## Compilation en exécutable Windows

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "PDF_Editor_Pro" "main.py"
```

## Structure du projet

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée de l'application |
| `main_window.py` | Fenêtre principale, barre d'outils et logique UI |
| `pdf_processor.py` | Opérations backend sur les PDF (lecture, écriture, fusion, division) |
| `pdf_canvas.py` | Zone d'affichage et d'édition par page |
| `page_manager.py` | Dialogue de gestion des pages |
| `signature_pad.py` | Dialogue de signature (dessin, import, réutilisation) |
| `icon.png` | Icône de l'application |
| `PDF Editor.spec` | Configuration PyInstaller |

## Technologies utilisées

- **PyQt6** — Interface graphique
- **PyMuPDF (fitz)** — Rendu et manipulation des PDF
- **pypdf** — Fusion et division de documents
- **PyInstaller** — Compilation en exécutable autonome
