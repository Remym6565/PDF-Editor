from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog, QMessageBox)
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt, QSize
import fitz
import os

class PageManagerDialog(QDialog):
    """
    Dialogue permettant de gérer visuellement les pages du document courant (réorganisation, fusion, division).
    """
    def __init__(self, processor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionnaire de Pages")
        self.resize(650, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ddd;
            }
            QLabel {
                color: #ddd;
                font-size: 13px;
            }
            QPushButton {
                background-color: #c7524a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #d97a73; }
            QPushButton:pressed { background-color: #b5433b; }
            QPushButton#dangerBtn {
                background-color: #c0392b;
            }
            QPushButton#dangerBtn:hover { background-color: #e74c3c; }
            QListWidget {
                background-color: #141414;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border: 2px solid transparent;
                border-radius: 6px;
                margin: 4px;
            }
            QListWidget::item:selected {
                background-color: #c7524a;
                border-color: #d97a73;
            }
            QListWidget::item:hover:!selected {
                background-color: #2a2a2a;
            }
        """)
        
        self.processor = processor
        
        # Copie de travail du document pour ne pas modifier l'original tant qu'on n'a pas fait "Appliquer"
        # On va travailler directement avec un document temporaire en mémoire
        if self.processor.doc:
            self.temp_doc = fitz.open()
            self.temp_doc.insert_pdf(self.processor.doc)
        else:
            self.temp_doc = fitz.open()

        layout = QVBoxLayout(self)

        # Liste des pages
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # Désactivation du Drag & Drop
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.list_widget.setIconSize(QSize(100, 140))
        self.list_widget.setSpacing(10)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        # Style déjà géré par le stylesheet général du dialogue
        
        layout.addWidget(self.list_widget)

        # Boutons de déplacement (Flèches)
        move_layout = QHBoxLayout()
        self.btn_move_left = QPushButton("◀ Déplacer à gauche")
        self.btn_move_right = QPushButton("Déplacer à droite ▶")
        self.btn_move_left.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_right.setCursor(Qt.CursorShape.PointingHandCursor)
        
        move_layout.addStretch()
        move_layout.addWidget(self.btn_move_left)
        move_layout.addWidget(self.btn_move_right)
        move_layout.addStretch()
        layout.addLayout(move_layout)

        # Boutons d'actions
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter un PDF")
        self.btn_extract = QPushButton("Extraire la sélection (Diviser)")
        self.btn_delete = QPushButton("Supprimer la sélection")
        self.btn_delete.setObjectName("dangerBtn")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_extract)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        # Boutons validation
        bottom_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_apply = QPushButton("Appliquer")
        self.btn_apply.setStyleSheet("background-color: #c7524a; color: white; font-weight: bold;")
        
        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_apply)
        layout.addLayout(bottom_layout)

        # Connexions
        self.btn_move_left.clicked.connect(self.move_item_left)
        self.btn_move_right.clicked.connect(self.move_item_right)
        self.btn_add.clicked.connect(self.add_pdf)
        self.btn_extract.clicked.connect(self.extract_pages)
        self.btn_delete.clicked.connect(self.delete_pages)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.apply_changes)

        self.load_thumbnails()

    def load_thumbnails(self):
        """Génère les miniatures pour le document temporaire."""
        self.list_widget.clear()
        
        for page_num in range(len(self.temp_doc)):
            page = self.temp_doc[page_num]
            # Basse résolution pour thumbnail rapide
            matrix = fitz.Matrix(0.2, 0.2)
            pix = page.get_pixmap(matrix=matrix)
            fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            
            pixmap = QPixmap.fromImage(img)
            
            # Pour associer le bon index original si besoin, on le stocke dans le texte ou les datas
            item = QListWidgetItem(f"Page {page_num + 1}")
            item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, page_num) # Index de la page dans le temp_doc
            self.list_widget.addItem(item)

    def add_pdf(self):
        """Ajoute les pages d'un autre PDF à la fin du document temporaire."""
        files, _ = QFileDialog.getOpenFileNames(self, "Sélectionner les PDF à ajouter", "", "Fichiers PDF (*.pdf)")
        if files:
            for file_path in files:
                try:
                    src_doc = fitz.open(file_path)
                    self.temp_doc.insert_pdf(src_doc)
                    src_doc.close()
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir {file_path}: {str(e)}")
            self.load_thumbnails()

    def extract_pages(self):
        """Extrait les pages sélectionnées vers un nouveau fichier PDF."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Veuillez sélectionner au moins une page.")
            return
            
        out_file, _ = QFileDialog.getSaveFileName(self, "Enregistrer les pages extraites", "", "Fichiers PDF (*.pdf)")
        if out_file:
            new_doc = fitz.open()
            # On récupère les indices des pages sélectionnées
            # L'utilisateur a pu les réorganiser visuellement, donc on extrait en fonction de la liste actuelle
            for item in selected_items:
                original_index = item.data(Qt.ItemDataRole.UserRole)
                new_doc.insert_pdf(self.temp_doc, from_page=original_index, to_page=original_index)
            
            new_doc.save(out_file)
            new_doc.close()
            QMessageBox.information(self, "Succès", "Les pages ont été extraites avec succès.")

    def delete_pages(self):
        """Supprime les pages sélectionnées de la liste (mais pas encore du temp_doc)."""
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            self.list_widget.takeItem(self.list_widget.row(item))

    def apply_changes(self):
        """Applique le nouvel ordre et supprime les pages manquantes au vrai document."""
        # Créer un document final vierge
        final_doc = fitz.open()
        
        # Parcourir la liste dans l'ordre visuel actuel
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            original_index = item.data(Qt.ItemDataRole.UserRole)
            final_doc.insert_pdf(self.temp_doc, from_page=original_index, to_page=original_index)
            
        # Mettre à jour le processeur
        if self.processor.doc:
            self.processor.doc.close()
            
        self.processor.doc = final_doc
        self.temp_doc.close()
        self.accept()

    def move_item_left(self):
        """Déplace la page sélectionnée vers la gauche (avant)."""
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row - 1, item)
            self.list_widget.setCurrentRow(current_row - 1)

    def move_item_right(self):
        """Déplace la page sélectionnée vers la droite (après)."""
        current_row = self.list_widget.currentRow()
        if current_row >= 0 and current_row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row + 1, item)
            self.list_widget.setCurrentRow(current_row + 1)
