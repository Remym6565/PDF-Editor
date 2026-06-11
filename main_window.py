from PyQt6.QtWidgets import (QMainWindow, QToolBar, QFileDialog, QMessageBox, 
                             QScrollArea, QVBoxLayout, QWidget, QDialog,
                             QFontComboBox, QSpinBox, QApplication,
                             QStatusBar, QLabel)
from PyQt6.QtGui import QAction, QKeySequence, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, QSize

from pdf_processor import PDFProcessor
from pdf_canvas import PDFCanvas
from signature_pad import SignaturePad
from page_manager import PageManagerDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Editor Pro")
        self.resize(1200, 800)
        
        # Style global
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            
            QToolBar {
                background-color: #222222;
                border: none;
                border-bottom: 1px solid #333;
                padding: 4px 8px;
                spacing: 4px;
            }
            QToolBar#textToolbar {
                background-color: #1e1e1e;
                border-bottom: 1px solid #333;
                padding: 4px 8px;
            }
            QToolButton {
                color: #ccc;
                padding: 6px 10px;
                border-radius: 6px;
                border: none;
                font-size: 12px;
                font-weight: 500;
            }
            QToolButton:hover { background-color: #333; color: #fff; }
            QToolButton:checked { background-color: #c7524a; color: #fff; }
            QToolButton:pressed { background-color: #2a2a2a; }
            
            QScrollArea { background-color: #141414; border: none; }
            QWidget#Container { background-color: #141414; }
            
            QMessageBox, QDialog {
                background-color: #1e1e1e; color: #ddd;
            }
            QLabel { color: #ddd; }
            
            QComboBox, QSpinBox, QFontComboBox {
                background-color: #2a2a2a;
                color: #ddd;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 24px;
            }
            QComboBox:hover, QSpinBox:hover, QFontComboBox:hover {
                border-color: #c7524a;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #ddd;
                selection-background-color: #c7524a;
                border: 1px solid #444;
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
            QPushButton:disabled { background-color: #333; color: #666; }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #6a6a6a;
                border: 1px solid #888;
                border-radius: 3px;
                width: 22px;
                margin: 1px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #c7524a;
                border-color: #d97a73;
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #b5433b;
            }
            
            QStatusBar {
                background-color: #1a1a1a;
                border-top: 1px solid #333;
                color: #888;
                font-size: 12px;
                padding: 2px 8px;
            }
        """)

        self.processor = PDFProcessor()
        
        # Zone de défilement pour les pages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.container_widget = QWidget()
        self.container_widget.setObjectName("Container")
        self.pages_layout = QVBoxLayout(self.container_widget)
        self.pages_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.pages_layout.setSpacing(30)
        self.scroll_area.setWidget(self.container_widget)
        
        self.setCentralWidget(self.scroll_area)
        
        self.canvases = []
        self.target_page_index = 0 # Page cible pour l'ajout de texte/image
        self.global_scale = 1.0
        
        self.create_actions()
        self.create_toolbar()
        self.current_text_item = None
        self.undo_stack = []
        
        self.status_label = QLabel("Prêt")
        self.statusBar().addWidget(self.status_label)
        
    def create_actions(self):
        self.act_new = QAction("Nouveau", self)
        self.act_new.triggered.connect(self.new_pdf)
        
        self.act_open = QAction("Ouvrir", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.open_pdf)
        
        self.act_save = QAction("Enregistrer", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self.save_pdf)
        
        self.act_edit_mode = QAction("Éditer", self)
        self.act_edit_mode.setCheckable(True)
        self.act_edit_mode.triggered.connect(self.toggle_edit_mode)
        
        self.act_add_text = QAction("Ajouter Texte", self)
        self.act_add_text.triggered.connect(self.add_text)
        
        self.act_add_image = QAction("Ajouter Image", self)
        self.act_add_image.triggered.connect(self.add_image)
        
        self.act_sign = QAction("Signer", self)
        self.act_sign.triggered.connect(self.open_signature_pad)
        
        self.act_undo = QAction("Annuler l'action", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.triggered.connect(self.undo_last_action)
        self.act_undo.setEnabled(False)
        
        self.act_page_manager = QAction("Gestionnaire de Pages", self)
        self.act_page_manager.triggered.connect(self.open_page_manager)
        
    def create_toolbar(self):
        toolbar = QToolBar("Barre d'outils principale")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.act_new)
        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_save)
        toolbar.addSeparator()
        toolbar.addAction(self.act_edit_mode)
        toolbar.addAction(self.act_add_text)
        toolbar.addAction(self.act_add_image)
        toolbar.addAction(self.act_sign)
        toolbar.addSeparator()
        toolbar.addAction(self.act_undo)
        toolbar.addSeparator()
        toolbar.addAction(self.act_page_manager)
        
        # Barre d'outils de formatage de texte (sur une nouvelle ligne)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.text_toolbar = QToolBar("Formatage Texte")
        self.text_toolbar.setObjectName("textToolbar")
        self.text_toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.text_toolbar)
        
        self.font_combo = QFontComboBox()
        self.font_combo.setEditable(False)
        self.font_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.font_combo.setMinimumWidth(150)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 100)
        self.size_spin.setValue(12)
        self.size_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.size_spin.setMinimumWidth(60)
        
        self.btn_bold = QAction("Gras", self)
        self.btn_bold.setCheckable(True)
        self.btn_bold.setToolTip("Gras (Ctrl+B)")
        
        self.btn_italic = QAction("Italique", self)
        self.btn_italic.setCheckable(True)
        self.btn_italic.setToolTip("Italique (Ctrl+I)")

        self.text_toolbar.addWidget(self.font_combo)
        self.text_toolbar.addWidget(self.size_spin)
        self.text_toolbar.addSeparator()
        self.text_toolbar.addAction(self.btn_bold)
        self.text_toolbar.addAction(self.btn_italic)
        
        self.text_toolbar.setVisible(False)
        
        self.font_combo.currentFontChanged.connect(self.set_text_font_family)
        self.size_spin.valueChanged.connect(self.set_text_font_size)
        self.btn_bold.toggled.connect(self.set_text_bold)
        self.btn_italic.toggled.connect(self.set_text_italic)

    def clear_pages(self):
        # Nettoyer l'ancien layout
        for i in reversed(range(self.pages_layout.count())): 
            widgetToRemove = self.pages_layout.itemAt(i).widget()
            self.pages_layout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)
        self.canvases.clear()
        self.global_scale = 1.0

    def update_view(self):
        if not self.processor.doc: return
        self.clear_pages()
        
        for i in range(self.processor.get_page_count()):
            canvas = PDFCanvas(page_index=i, parent=self)
            
            image = self.processor.get_page_image(i, zoom=3.0)
            edit_mode = self.act_edit_mode.isChecked()
            canvas.edit_mode_active = edit_mode
            
            if image:
                canvas.set_pdf_page(image)
            
            if edit_mode:
                text_blocks = self.processor.get_text_blocks(i)
                image_blocks = self.processor.get_image_blocks(i)
                canvas.show_edit_overlays(text_blocks, image_blocks)
                
            canvas.zoom_requested.connect(self.handle_zoom)
            canvas.clicked_signal.connect(self.set_target_page)
            canvas.scene.selectionChanged.connect(self.on_selection_changed)
            canvas.undo_requested.connect(self.push_undo)
            
            self.pages_layout.addWidget(canvas)
            self.canvases.append(canvas)
            
        self.setWindowTitle(f"PDF Editor - {self.processor.get_page_count()} pages")
        self.target_page_index = 0

    def set_target_page(self, index):
        """Définit la page qui recevra le prochain ajout d'image/texte."""
        self.target_page_index = index

    def on_selection_changed(self):
        selected_text_item = None
        from pdf_canvas import MovableTextItem
        for canvas in self.canvases:
            for item in canvas.scene.selectedItems():
                if isinstance(item, MovableTextItem):
                    selected_text_item = item
                    break
            if selected_text_item: break
            
        if selected_text_item:
            self.current_text_item = selected_text_item
            # Afficher la police actuelle du texte à la position du curseur
            cursor = selected_text_item.textCursor()
            char_format = cursor.charFormat()
            font = char_format.font()
            
            self.font_combo.blockSignals(True)
            self.size_spin.blockSignals(True)
            self.btn_bold.blockSignals(True)
            self.btn_italic.blockSignals(True)
            
            self.font_combo.setCurrentFont(font)
            self.size_spin.setValue(max(8, font.pointSize()))
            self.btn_bold.setChecked(font.bold())
            self.btn_italic.setChecked(font.italic())
            
            self.font_combo.blockSignals(False)
            self.size_spin.blockSignals(False)
            self.btn_bold.blockSignals(False)
            self.btn_italic.blockSignals(False)
            self.text_toolbar.setVisible(True)
            self.text_toolbar.setEnabled(True)
        else:
            # Différer le nettoyage pour laisser le focus se déplacer vers la toolbar
            QTimer.singleShot(150, self._deferred_clear_text_item)

    def _deferred_clear_text_item(self):
        """Vérifie (après délai) si le focus est bien en dehors de la toolbar avant de la masquer."""
        fw = QApplication.focusWidget()
        in_toolbar = (fw is not None and (
            fw is self.font_combo or
            fw is self.size_spin or
            self.text_toolbar.isAncestorOf(fw)
        ))
        if not in_toolbar:
            self.current_text_item = None
            if not self.act_edit_mode.isChecked():
                self.text_toolbar.setVisible(False)
            self.text_toolbar.setEnabled(False)

    def set_text_font_family(self, font):
        from PyQt6.QtGui import QTextCharFormat
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self._apply_text_format(fmt)

    def set_text_font_size(self, size):
        from PyQt6.QtGui import QTextCharFormat
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._apply_text_format(fmt)

    def set_text_bold(self, checked):
        from PyQt6.QtGui import QTextCharFormat, QFont
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._apply_text_format(fmt)

    def set_text_italic(self, checked):
        from PyQt6.QtGui import QTextCharFormat
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._apply_text_format(fmt)

    def _apply_text_format(self, fmt):
        """Applique une propriété spécifique sans écraser les autres."""
        if not self.current_text_item:
            return
        from PyQt6.QtGui import QTextCursor
        cursor = self.current_text_item.textCursor()
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
            self.current_text_item.setTextCursor(cursor)
        else:
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.mergeCharFormat(fmt)
            cursor.clearSelection()
            self.current_text_item.setTextCursor(cursor)

    def handle_zoom(self, factor):
        """Applique le zoom à tous les canevas."""
        self.global_scale *= factor
        for canvas in self.canvases:
            canvas.resetTransform()
            canvas.scale(self.global_scale, self.global_scale)
            # Utiliser la taille de l'image de fond pour éviter l'agrandissement incontrôlé dû aux éléments hors cadre
            if canvas.background_item:
                orig_size = canvas.background_item.boundingRect().size()
                new_w = int(orig_size.width() * self.global_scale)
                new_h = int(orig_size.height() * self.global_scale)
                canvas.setFixedSize(new_w, new_h)

    def fit_to_height(self):
        """Zoom pour ajuster une page à 100% de la hauteur de l'écran avec une marge."""
        if not self.canvases: return
        first_canvas = self.canvases[0]
        if first_canvas.background_item:
            scene_height = first_canvas.background_item.boundingRect().height()
            if scene_height > 0:
                scroll_height = self.scroll_area.viewport().height() - 20 # marge
                self.global_scale = scroll_height / scene_height
                for canvas in self.canvases:
                    canvas.resetTransform()
                    canvas.scale(self.global_scale, self.global_scale)
                    orig_size = canvas.background_item.boundingRect().size()
                    new_w = int(orig_size.width() * self.global_scale)
                    new_h = int(orig_size.height() * self.global_scale)
                    canvas.setFixedSize(new_w, new_h)

    def toggle_edit_mode(self, checked):
        """Active/désactive le mode édition sans recharger la vue (les modifs sont préservées)."""
        edit_mode = checked
        for i, canvas in enumerate(self.canvases):
            canvas.edit_mode_active = edit_mode
            if edit_mode:
                # Charger et afficher les overlays
                text_blocks = self.processor.get_text_blocks(i)
                image_blocks = self.processor.get_image_blocks(i)
                canvas.show_edit_overlays(text_blocks, image_blocks)
            else:
                # Cacher les overlays sans toucher aux textes/images ajoutés
                canvas.hide_edit_overlays()
        
        if checked:
            self.text_toolbar.setVisible(True)
            self.text_toolbar.setEnabled(True)
        else:
            self.text_toolbar.setVisible(False)

    def new_pdf(self):
        self.processor.create_new_pdf()
        self.update_view()

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir PDF", "", "Fichiers PDF (*.pdf)")
        if file_path:
            self.processor.open_pdf(file_path)
            self.update_view()
            self.fit_to_height()

    def save_pdf(self):
        if not self.processor.doc:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF", "", "Fichiers PDF (*.pdf)")
        if file_path:
            mods = {}
            for i, canvas in enumerate(self.canvases):
                page_mods = canvas.get_export_data()
                if page_mods:
                    mods[i] = page_mods
                    
            if self.processor.save_pdf(file_path, mods):
                QMessageBox.information(self, "Succès", "Le fichier a été enregistré avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de l'enregistrement.")

    def push_undo(self, undo_func):
        """Ajoute une action à la pile d'annulation."""
        if callable(undo_func):
            self.undo_stack.append(undo_func)
            self.act_undo.setEnabled(True)

    def undo_last_action(self):
        """Annule la dernière action de création."""
        if self.undo_stack:
            undo_func = self.undo_stack.pop()
            undo_func()
            if not self.undo_stack:
                self.act_undo.setEnabled(False)

    def add_text(self):
        if self.canvases:
            undo_func = self.canvases[self.target_page_index].add_text()
            self.push_undo(undo_func)
            self.text_toolbar.setVisible(True) # Ouvre la barre pour le nouveau texte

    def add_image(self):
        if self.canvases:
            file_path, _ = QFileDialog.getOpenFileName(self, "Insérer une image", "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                undo_func = self.canvases[self.target_page_index].add_image(file_path)
                if undo_func:
                    self.push_undo(undo_func)

    def open_signature_pad(self):
        if self.canvases:
            dialog = SignaturePad(self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.signature_path:
                undo_func = self.canvases[self.target_page_index].add_image(dialog.signature_path)
                if undo_func:
                    self.push_undo(undo_func)

    def open_page_manager(self):
        if not self.processor.doc:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord ouvrir un document.")
            return
            
        dialog = PageManagerDialog(self.processor, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_view()
            self.fit_to_height()
