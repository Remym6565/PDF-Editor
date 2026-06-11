# 📄 PDF Editor Pro

> Un éditeur PDF moderne, gratuit et open source pour Windows.

<p align="center">
  <a href="https://remym6565.github.io/PDF-Editor/">
    <img src="https://img.shields.io/badge/Landing%20Page-Visiter-7b68ee?style=for-the-badge" alt="Landing Page">
  </a>
  <a href="https://github.com/Remym6565/PDF-Editor/releases/download/v1.0.1/PDF_Editor_Pro.exe">
    <img src="https://img.shields.io/badge/T%C3%A9l%C3%A9charger-61%20Mo-00d2ff?style=for-the-badge" alt="Télécharger">
  </a>
  <a href="https://github.com/Remym6565/PDF-Editor">
    <img src="https://img.shields.io/badge/Code-GitHub-333?style=for-the-badge" alt="GitHub">
  </a>
</p>

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
| --- | --- |
| ✏️ **Texte & Typographie** | Ajout de texte avec police, taille, gras, italique et couleur |
| 🖼️ **Images & Signatures** | Insertion d'images, dessin ou import de signature |
| 📑 **Gestionnaire de pages** | Réorganisation, fusion et division visuelles |
| ⚡ **Rapide & Léger** | Application native Windows, exécutable autonome |
| 🎨 **Interface moderne** | Thème sombre élégant, zoom ajustable |
| ↩️ **Annulation (Undo)** | Ctrl+Z pour revenir en arrière |

---

## 🚀 Installation

```bash
pip install PyQt6 PyMuPDF pypdf
```

```bash
python main.py
```

## 📦 Compilation en exécutable

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "PDF_Editor_Pro" "main.py"
```

---

## 📁 Structure

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée |
| `main_window.py` | Fenêtre principale, barre d'outils |
| `pdf_processor.py` | Opérations PDF (lecture, écriture, fusion) |
| `pdf_canvas.py` | Affichage et édition par page |
| `page_manager.py` | Gestionnaire de pages |
| `signature_pad.py` | Dialogue de signature |

## 🛠️ Technologies

- **PyQt6** — Interface graphique
- **PyMuPDF (fitz)** — Rendu et manipulation PDF
- **pypdf** — Fusion et division
- **PyInstaller** — Compilation exécutable
