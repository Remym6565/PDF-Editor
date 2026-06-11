from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QGraphicsView, QGraphicsScene, QCheckBox, 
                             QFileDialog, QMessageBox, QTabWidget, QWidget, QLabel)
from PyQt6.QtGui import QPen, QPainter, QImage, QColor, QPixmap
from PyQt6.QtCore import Qt, QPointF
import os
import shutil

class SignaturePad(QDialog):
    """
    Fenêtre de dialogue ergonomique avec onglets pour dessiner, importer ou réutiliser une signature.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une signature")
        self.setFixedSize(550, 470)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ddd;
            }
            QLabel {
                color: #ddd;
                font-size: 13px;
            }
            QTabWidget::pane {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 12px;
            }
            QTabBar::tab {
                background-color: #222;
                color: #888;
                padding: 8px 16px;
                border: 1px solid #333;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                color: #c7524a;
                border-bottom: 2px solid #c7524a;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2a2a2a;
                color: #ddd;
            }
            QPushButton {
                background-color: #c7524a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #d97a73; }
            QPushButton:pressed { background-color: #b5433b; }
            QCheckBox {
                color: #aaa;
                spacing: 8px;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555;
                border-radius: 4px;
                background-color: #222;
            }
            QCheckBox::indicator:checked {
                background-color: #c7524a;
                border-color: #c7524a;
            }
        """)
        self.signature_path = None

        self.save_dir = os.path.join(os.path.expanduser("~"), ".pdf_editor_signatures")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        self.reference_path = os.path.join(self.save_dir, "reference.png")

        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { font-size: 14px; padding: 8px 15px; }")
        main_layout.addWidget(self.tabs)

        # TAB 1: Référence (si existante)
        self.tab_ref = QWidget()
        ref_layout = QVBoxLayout(self.tab_ref)
        if os.path.exists(self.reference_path):
            lbl_title = QLabel("Signature Enregistrée")
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
            ref_layout.addWidget(lbl_title)
            
            preview_img = QLabel()
            pix = QPixmap(self.reference_path)
            pix = pix.scaled(400, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            preview_img.setPixmap(pix)
            preview_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_img.setStyleSheet("background-color: #f9f9f9; border: 2px dashed #c7524a; border-radius: 10px; padding: 10px;")
            ref_layout.addWidget(preview_img)
            
            self.btn_use_ref = QPushButton("Utiliser cette signature")
            self.btn_use_ref.setStyleSheet("background-color: #c7524a; color: white; font-size: 14px; font-weight: bold; padding: 10px; border-radius: 5px;")
            self.btn_use_ref.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_use_ref.clicked.connect(self.use_reference)
            ref_layout.addSpacing(20)
            ref_layout.addWidget(self.btn_use_ref)
            ref_layout.addStretch()
        else:
            lbl_empty = QLabel("Aucune signature enregistrée pour le moment.\nUtilisez les autres onglets pour en créer une.")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("color: #666; font-size: 14px;")
            ref_layout.addWidget(lbl_empty)
            
        self.tabs.addTab(self.tab_ref, "Signature Enregistrée")

        # TAB 2: Dessiner
        self.tab_draw = QWidget()
        draw_layout = QVBoxLayout(self.tab_draw)
        
        self.scene = QGraphicsScene(0, 0, 500, 200)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 5px;")
        draw_layout.addWidget(self.view)
        
        self.chk_reference_draw = QCheckBox("Enregistrer comme signature par défaut")
        self.chk_reference_draw.setChecked(True)
        draw_layout.addWidget(self.chk_reference_draw)
        
        btn_layout_draw = QHBoxLayout()
        self.btn_clear = QPushButton("Effacer le dessin")
        self.btn_save_draw = QPushButton("Valider la signature")
        self.btn_save_draw.setStyleSheet("background-color: #107C10; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px;")
        self.btn_save_draw.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_layout_draw.addWidget(self.btn_clear)
        btn_layout_draw.addStretch()
        btn_layout_draw.addWidget(self.btn_save_draw)
        draw_layout.addLayout(btn_layout_draw)
        
        self.tabs.addTab(self.tab_draw, "Dessiner")

        # TAB 3: Importer
        self.tab_import = QWidget()
        import_layout = QVBoxLayout(self.tab_import)
        
        lbl_import = QLabel("Importez une image contenant votre signature (fond transparent recommandé).")
        lbl_import.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_import.setWordWrap(True)
        lbl_import.setStyleSheet("font-size: 14px; margin: 20px;")
        import_layout.addWidget(lbl_import)
        
        self.chk_reference_import = QCheckBox("Enregistrer comme signature par défaut")
        self.chk_reference_import.setChecked(True)
        import_layout.addWidget(self.chk_reference_import, alignment=Qt.AlignmentFlag.AlignCenter)
        
        import_layout.addSpacing(20)
        self.btn_import = QPushButton("Parcourir et Importer...")
        self.btn_import.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        import_layout.addWidget(self.btn_import, alignment=Qt.AlignmentFlag.AlignCenter)
        import_layout.addStretch()
        
        self.tabs.addTab(self.tab_import, "Importer")

        # Sélectionner par défaut le premier onglet s'il y a une référence, sinon le dessin
        if not os.path.exists(self.reference_path):
            self.tabs.setCurrentIndex(1)

        # Événements
        self.btn_clear.clicked.connect(self.clear_pad)
        self.btn_save_draw.clicked.connect(self.save_drawn_signature)
        self.btn_import.clicked.connect(self.import_signature)

        # Variables d'état pour le dessin
        self.drawing = False
        self.last_point = None
        self.pen = QPen(Qt.GlobalColor.black, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

        self.view.mousePressEvent = self.mousePressEvent
        self.view.mouseMoveEvent = self.mouseMoveEvent
        self.view.mouseReleaseEvent = self.mouseReleaseEvent

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = self.view.mapToScene(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and self.last_point:
            current_point = self.view.mapToScene(event.pos())
            self.scene.addLine(self.last_point.x(), self.last_point.y(), 
                               current_point.x(), current_point.y(), self.pen)
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.last_point = None

    def clear_pad(self):
        self.scene.clear()

    def save_drawn_signature(self):
        if not self.scene.items():
            QMessageBox.warning(self, "Erreur", "Le dessin est vide.")
            return

        image = QImage(self.scene.sceneRect().size().toSize(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter)
        painter.end()

        file_path = os.path.join(self.save_dir, "signature_temp.png")
        image.save(file_path)
        
        if self.chk_reference_draw.isChecked():
            image.save(self.reference_path)
            
        self.signature_path = file_path
        self.accept()

    def import_signature(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner l'image de la signature", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            if self.chk_reference_import.isChecked():
                shutil.copy(file_path, self.reference_path)
            self.signature_path = file_path
            self.accept()

    def use_reference(self):
        self.signature_path = self.reference_path
        self.accept()
