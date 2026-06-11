# Instructions de Compilation avec PyInstaller

Ce document décrit comment compiler l'application `PDF Editor Pro` en un unique fichier exécutable `.exe` pour Windows.

## Prérequis

1. Assurez-vous que Python est installé.
2. Ouvrez une invite de commande (CMD ou PowerShell) dans le dossier du projet (`C:\Users\REMY\Documents\PDF\PDF_Editor`).
3. Installez PyInstaller ainsi que les dépendances du projet :
   ```bash
   pip install PyQt6 PyMuPDF pypdf pyinstaller
   ```

## Commande de Compilation Rapide

Pour générer un seul fichier `.exe` qui s'exécute sans ouvrir de console (mode fenêtré), exécutez la commande suivante :

```bash
pyinstaller --noconfirm --onedir --windowed --name "PDF_Editor_Pro"  "main.py"
```

*Note : Bien que `--onefile` permette d'avoir un fichier unique, pour des applications PyQt6 avec PyMuPDF, l'utilisation de `--onedir` (par défaut) est fortement recommandée dans un premier temps pour éviter les lenteurs de démarrage causées par l'extraction des lourdes bibliothèques dans un dossier temporaire à chaque lancement. Si vous tenez absolument à un fichier unique, utilisez `--onefile`.*

Pour un exécutable strict "Un seul fichier" :
```bash
pyinstaller --noconfirm --onefile --windowed --name "PDF_Editor_Pro"  "main.py"
```

## Structure générée

Après la compilation, PyInstaller créera deux dossiers :
- `build/` : Dossier de travail temporaire (peut être supprimé).
- `dist/` : Contient l'application finale compilée.

Dans le dossier `dist/`, vous trouverez soit votre dossier `PDF_Editor_Pro` (si vous avez utilisé `--onedir`), soit directement votre fichier `PDF_Editor_Pro.exe` (si vous avez utilisé `--onefile`).

## Ajout d'une icône personnalisée
Si vous souhaitez ajouter une icône à votre application, placez votre fichier `.ico` (ex: `icon.ico`) dans le dossier du projet et ajoutez le flag `--icon` :

```bash
pyinstaller --noconfirm --onefile --windowed --icon "icon.ico" --name "PDF_Editor_Pro" "main.py"
```
