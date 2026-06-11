from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
                             QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QFont, QColor, QPen, QBrush, QCursor
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
import tempfile, os

class MovableTextItem(QGraphicsTextItem):
    """Texte déplaçable (simple clic) et éditable en riche (double clic)."""
    def __init__(self, text, is_original=False, original_rect=None, is_html=False, parent=None):
        super().__init__(parent)
        if is_html:
            self.setHtml(text)
        else:
            self.setPlainText(text)
            self.setFont(QFont("Arial", 12))
            self.setDefaultTextColor(QColor("black"))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        # Mode par défaut : déplaçable, pas d'édition de texte
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.is_original = is_original
        self.original_rect = original_rect
        self.editing = False

    def mouseDoubleClickEvent(self, event):
        """Double-clic : entrer en mode édition riche."""
        if not self.editing:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.editing = True
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        super().mouseDoubleClickEvent(event)
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.editing:
            self._exit_edit_mode()
        else:
            super().keyPressEvent(event)

    def _exit_edit_mode(self):
        """Quitter le mode édition, repasser en mode déplacement."""
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.editing = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.clearFocus()

    def focusOutEvent(self, event):
        """Désactive l'édition si on clique en dehors du texte."""
        if self.editing:
            self._exit_edit_mode()
        super().focusOutEvent(event)

class MovableImageItem(QGraphicsPixmapItem):
    """Élément d'image déplaçable avec poignée de redimensionnement améliorée."""
    def __init__(self, pixmap, path="", parent=None):
        super().__init__(pixmap, parent)
        self.path = path
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setAcceptHoverEvents(True)
        self.resizing = False
        self.handle_size = 25  # Poignée plus grande pour faciliter la sélection

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        # Dessiner la poignée si sélectionné
        if self.isSelected():
            rect = self.boundingRect()
            painter.setBrush(QBrush(QColor(0, 120, 215, 200))) # Légèrement transparent
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            handle_rect = QRectF(rect.right() - self.handle_size, rect.bottom() - self.handle_size, self.handle_size, self.handle_size)
            painter.drawRect(handle_rect)

    def hoverMoveEvent(self, event):
        if self.isSelected():
            rect = self.boundingRect()
            handle_rect = QRectF(rect.right() - self.handle_size, rect.bottom() - self.handle_size, self.handle_size, self.handle_size)
            if handle_rect.contains(event.pos()):
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        rect = self.boundingRect()
        handle_rect = QRectF(rect.right() - self.handle_size, rect.bottom() - self.handle_size, self.handle_size, self.handle_size)
        if handle_rect.contains(event.pos()) and self.isSelected():
            self.resizing = True
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            # Utiliser les coordonnées de la scène pour éviter la boucle de feedback due au changement de scale interne
            new_width = max(20.0, event.scenePos().x() - self.scenePos().x())
            new_height = max(20.0, event.scenePos().y() - self.scenePos().y())
            
            original_size = self.pixmap().size()
            scale_x = new_width / original_size.width()
            scale_y = new_height / original_size.height()
            
            scale = max(scale_x, scale_y)
            self.setScale(scale)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class ImageBlockOverlay(QGraphicsRectItem):
    """Rectangle interactif au-dessus d'une image existante."""
    def __init__(self, rect, image_xref, canvas, parent=None):
        super().__init__(rect, parent)
        self.canvas = canvas
        self.image_xref = image_xref
        self.original_rect = rect
        
        self.setPen(QPen(QColor(255, 140, 0, 200), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(255, 140, 0, 40)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.canvas.make_image_movable(self)

class TextBlockOverlay(QGraphicsRectItem):
    """Rectangle interactif au-dessus d'un texte existant."""
    def __init__(self, rect, text, canvas, raw_block=None, parent=None):
        super().__init__(rect, parent)
        self.canvas = canvas
        self.text_content = text
        self.original_rect = rect
        self.raw_block = raw_block
        
        self.setPen(QPen(QColor(0, 120, 215, 150), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(0, 120, 215, 50)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.canvas.edit_existing_text(self)

class PDFCanvas(QGraphicsView):
    """
    Composant affichant UNE SEULE page PDF.
    Les multiples pages seront gérées par main_window.
    """
    zoom_requested = pyqtSignal(float)
    clicked_signal = pyqtSignal(int)  # Emis quand on clique sur cette page
    undo_requested = pyqtSignal(object)  # Emis avec une fonction d'annulation

    def __init__(self, page_index, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # On désactive le scroll interne pour que le QScrollArea parent prenne le relais
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setDragMode(QGraphicsView.DragMode.NoDrag) # Laisser le scroll au parent
        
        self.background_item = None
        self.zoom_factor = 3.0
        
        self.redactions = []
        self.image_redactions = []  # rects des images supprimées/déplacées
        self.edit_mode_active = False
        self.text_block_overlays = []
        self.image_block_overlays = []
        
        # Style pour s'intégrer au fond
        self.setStyleSheet("background-color: transparent; border: 1px solid #333;")

    def wheelEvent(self, event):
        """Redirige le zoom Ctrl+Molette vers main_window pour zoomer toutes les pages."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.zoom_requested.emit(factor)
            event.accept()
        else:
            # Laisser l'événement remonter au QScrollArea parent pour le défilement normal
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene.selectedItems():
                if isinstance(item, (MovableTextItem, MovableImageItem)):
                    self.scene.removeItem(item)
            # Ne pas appeler accept() pour laisser les autres composants traiter si besoin
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Signaler à main_window que cette page a été cliquée (pour savoir où ajouter textes/images)
        self.clicked_signal.emit(self.page_index)
        super().mousePressEvent(event)

    def set_pdf_page(self, qimage, text_blocks=None, image_blocks=None):
        """Affiche l'image de la page en arrière-plan."""
        self.scene.clear()
        self.text_block_overlays.clear()
        self.image_block_overlays.clear()
        
        pixmap = QPixmap.fromImage(qimage)
        self.background_item = self.scene.addPixmap(pixmap)
        self.background_item.setZValue(-1)
        self.setSceneRect(QRectF(pixmap.rect()))
        
        # Ajuster la taille du composant QGraphicsView pour correspondre à la scène
        self.setFixedSize(pixmap.size())

        if self.edit_mode_active:
            if text_blocks:
                for block in text_blocks:
                    rect = block['rect']
                    already_edited = False
                    for r in self.redactions:
                        if abs(r[0] - rect[0]) < 2 and abs(r[1] - rect[1]) < 2:
                            already_edited = True
                            break
                    
                    if not already_edited:
                        scaled_rect = QRectF(rect[0] * self.zoom_factor, 
                                             rect[1] * self.zoom_factor, 
                                             (rect[2] - rect[0]) * self.zoom_factor, 
                                             (rect[3] - rect[1]) * self.zoom_factor)
                        overlay = TextBlockOverlay(scaled_rect, block['text'], self)
                        self.scene.addItem(overlay)
                        self.text_block_overlays.append(overlay)
            
            if image_blocks:
                for block in image_blocks:
                    rect = block['rect']
                    scaled_rect = QRectF(rect[0] * self.zoom_factor,
                                         rect[1] * self.zoom_factor,
                                         (rect[2] - rect[0]) * self.zoom_factor,
                                         (rect[3] - rect[1]) * self.zoom_factor)
                    overlay = ImageBlockOverlay(scaled_rect, block.get('xref', 0), self)
                    self.scene.addItem(overlay)
                    self.image_block_overlays.append(overlay)

    def toggle_edit_mode(self, active, text_blocks=None):
        self.edit_mode_active = active

    def show_edit_overlays(self, text_blocks, image_blocks=None):
        """Affiche les overlays d'édition sans recharger la page."""
        # Supprimer les anciens overlays s'il y en a
        self.hide_edit_overlays()
        
        if text_blocks:
            for block in text_blocks:
                rect = block['rect']
                # Ne pas re-créer un overlay si ce texte a déjà été édité
                already_edited = any(
                    abs(r[0] - rect[0]) < 2 and abs(r[1] - rect[1]) < 2
                    for r in self.redactions
                )
                if not already_edited:
                    scaled_rect = QRectF(
                        rect[0] * self.zoom_factor, rect[1] * self.zoom_factor,
                        (rect[2] - rect[0]) * self.zoom_factor, (rect[3] - rect[1]) * self.zoom_factor
                    )
                    overlay = TextBlockOverlay(
                        scaled_rect, block['text'], self,
                        raw_block=block.get('raw_block')
                    )
                    self.scene.addItem(overlay)
                    self.text_block_overlays.append(overlay)
        
        if image_blocks:
            for block in image_blocks:
                rect = block['rect']
                scaled_rect = QRectF(
                    rect[0] * self.zoom_factor, rect[1] * self.zoom_factor,
                    (rect[2] - rect[0]) * self.zoom_factor, (rect[3] - rect[1]) * self.zoom_factor
                )
                overlay = ImageBlockOverlay(scaled_rect, block.get('xref', 0), self)
                self.scene.addItem(overlay)
                self.image_block_overlays.append(overlay)

    def hide_edit_overlays(self):
        """Cache et supprime tous les overlays d'édition de la scène."""
        for overlay in self.text_block_overlays:
            self.scene.removeItem(overlay)
        self.text_block_overlays.clear()
        for overlay in self.image_block_overlays:
            self.scene.removeItem(overlay)
        self.image_block_overlays.clear()

    def edit_existing_text(self, overlay):
        orig_r = overlay.original_rect
        unscaled_rect = (orig_r.x() / self.zoom_factor, 
                         orig_r.y() / self.zoom_factor, 
                         (orig_r.x() + orig_r.width()) / self.zoom_factor, 
                         (orig_r.y() + orig_r.height()) / self.zoom_factor)
        
        self.redactions.append(unscaled_rect)
        
        white_rect = QGraphicsRectItem(orig_r)
        white_rect.setBrush(QBrush(Qt.GlobalColor.white))
        white_rect.setPen(QPen(Qt.PenStyle.NoPen))
        white_rect.setZValue(-0.5)
        self.scene.addItem(white_rect)
        
        # --- Génération du HTML riche depuis raw_block ---
        html_content = ""
        if hasattr(overlay, 'raw_block') and overlay.raw_block:
            import html
            last_y0 = None
            last_x1 = None
            
            for line in overlay.raw_block.get("lines", []):
                y0 = line.get("bbox", [0,0,0,0])[1]
                if html_content:
                    if last_y0 is not None and abs(y0 - last_y0) < 12.0 * 0.5:
                        pass
                    else:
                        html_content += "<br>"
                        last_x1 = None
                last_y0 = y0
                
                for span in line.get("spans", []):
                    x0 = span.get("bbox", [0,0,0,0])[0]
                    if last_x1 is not None and (x0 - last_x1) > span.get("size", 12.0) * 0.2:
                        spaces = max(1, int((x0 - last_x1) / (span.get("size", 12.0) * 0.25)))
                        html_content += "&nbsp;" * spaces
                    
                    fname = span.get("font", "Arial")
                    if "+" in fname:
                        fname = fname.split("+", 1)[1]
                    
                    fname_lower = fname.lower()
                    if 'times' in fname_lower or 'roman' in fname_lower:
                        qt_family = 'Times New Roman'
                    elif 'courier' in fname_lower:
                        qt_family = 'Courier New'
                    elif 'helvetica' in fname_lower or 'arial' in fname_lower:
                        qt_family = 'Arial'
                    elif 'calibri' in fname_lower:
                        qt_family = 'Calibri'
                    elif 'cambria' in fname_lower:
                        qt_family = 'Cambria'
                    elif 'segoe' in fname_lower:
                        qt_family = 'Segoe UI'
                    else:
                        qt_family = fname.split("-")[0].split(",")[0]
                    
                    qt_size = max(6, int(span.get("size", 12.0) * self.zoom_factor * 0.75))
                    
                    color_int = span.get("color", 0)
                    r = (color_int >> 16) & 0xFF
                    g = (color_int >> 8) & 0xFF
                    b = color_int & 0xFF
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                    
                    flags = span.get("flags", 0)
                    fname_lower = fname.lower()
                    is_bold = bool(flags & 16) or "bold" in fname_lower or "black" in fname_lower
                    is_italic = bool(flags & 2) or "italic" in fname_lower or "oblique" in fname_lower
                    
                    safe_text = html.escape(span.get("text", "")).replace(" ", "&nbsp;")
                    
                    span_html = f'<span style="font-family: \'{qt_family}\'; font-size: {qt_size}pt; color: {color_hex};">'
                    if is_bold: span_html += '<b>'
                    if is_italic: span_html += '<i>'
                    span_html += safe_text
                    if is_italic: span_html += '</i>'
                    if is_bold: span_html += '</b>'
                    span_html += '</span>'
                    
                    html_content += span_html
                    last_x1 = span.get("bbox", [0,0,0,0])[2]
        else:
            # Fallback simple
            import html
            safe_text = html.escape(overlay.text_content).replace('\n', '<br>').replace(' ', '&nbsp;')
            html_content = f'<span style="font-family: Arial; font-size: {int(12*self.zoom_factor*0.75)}pt; color: black;">{safe_text}</span>'
            
        text_item = MovableTextItem(html_content, is_original=True, original_rect=unscaled_rect, is_html=True)
        text_item.setPos(orig_r.x(), orig_r.y() - 5) # Ajustement léger pour le padding HTML
        self.scene.addItem(text_item)
        
        self.scene.removeItem(overlay)
        if overlay in self.text_block_overlays:
            self.text_block_overlays.remove(overlay)
            
        def undo_edit():
            if unscaled_rect in self.redactions:
                self.redactions.remove(unscaled_rect)
            self.scene.removeItem(white_rect)
            self.scene.removeItem(text_item)
            self.scene.addItem(overlay)
            if overlay not in self.text_block_overlays:
                self.text_block_overlays.append(overlay)
                
        return undo_edit

    def make_image_movable(self, overlay):
        """Transforme une image existante du PDF en élément déplaçable."""
        orig_r = overlay.original_rect
        
        # Copier l'image depuis la scène (le canvas de fond)
        # On extrait le pixmap directement depuis le background_item de la page courante
        # en récupérant la portion correspondante à la zone de l'image
        src_pixmap = self.background_item.pixmap().copy(
            int(orig_r.x()), int(orig_r.y()), int(orig_r.width()), int(orig_r.height())
        )
        
        # Couvrir l'image originale d'un rectangle blanc (rédaction)
        unscaled_rect = (orig_r.x() / self.zoom_factor,
                         orig_r.y() / self.zoom_factor,
                         (orig_r.x() + orig_r.width()) / self.zoom_factor,
                         (orig_r.y() + orig_r.height()) / self.zoom_factor)
        self.image_redactions.append(unscaled_rect)
        
        white_rect = QGraphicsRectItem(orig_r)
        white_rect.setBrush(QBrush(Qt.GlobalColor.white))
        white_rect.setPen(QPen(Qt.PenStyle.NoPen))
        white_rect.setZValue(0)
        self.scene.addItem(white_rect)
        
        # Sauvegarder le pixmap dans un fichier temp pour pouvoir le réexporter dans le PDF
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"pdf_edit_img_{id(overlay)}.png")
        src_pixmap.save(tmp_path, "PNG")
        
        # Créer un MovableImageItem avec le fichier temporaire
        image_item = MovableImageItem(src_pixmap, path=tmp_path)
        image_item.setPos(orig_r.x(), orig_r.y())
        self.scene.addItem(image_item)
        
        # Supprimer l'overlay
        self.scene.removeItem(overlay)
        if overlay in self.image_block_overlays:
            self.image_block_overlays.remove(overlay)
        
        def undo_make_movable():
            if unscaled_rect in self.image_redactions:
                self.image_redactions.remove(unscaled_rect)
            self.scene.removeItem(white_rect)
            self.scene.removeItem(image_item)
            self.scene.addItem(overlay)
            if overlay not in self.image_block_overlays:
                self.image_block_overlays.append(overlay)
                
        self.undo_requested.emit(undo_make_movable)
        return undo_make_movable

    def add_text(self):
        text_item = MovableTextItem("Double-cliquez pour éditer")
        view_center = self.mapToScene(self.viewport().rect().center())
        text_item.setPos(view_center)
        self.scene.addItem(text_item)
        
        def undo_add_text():
            self.scene.removeItem(text_item)
            
        return undo_add_text

    def add_image(self, image_path):
        pixmap = QPixmap(image_path)
        if pixmap.isNull(): return None
        
        image_item = MovableImageItem(pixmap, path=image_path)
        view_center = self.mapToScene(self.viewport().rect().center())
        image_item.setPos(view_center)
        self.scene.addItem(image_item)
        
        def undo_add_image():
            self.scene.removeItem(image_item)
            
        return undo_add_image

    def get_export_data(self):
        """Extrait les données (ajouts/redactions) pour cette page spécifique."""
        page_mods = []
        
        for rect in self.redactions:
            page_mods.append({
                'type': 'redact',
                'rect': rect
            })
        
        # Rédactions des images existantes déplacées
        for rect in self.image_redactions:
            page_mods.append({
                'type': 'redact',
                'rect': rect
            })
            
        for item in self.scene.items():
            if isinstance(item, MovableTextItem):
                if not item.toPlainText().strip() and item.is_original:
                    continue
                pos = item.scenePos()
                color = item.defaultTextColor()
                font = item.font()
                page_mods.append({
                    'type': 'text',
                    'x': pos.x() / self.zoom_factor,
                    'y': (pos.y() + font.pointSize() * 1.5) / self.zoom_factor, 
                    'text': item.toPlainText(),
                    'color': (color.red(), color.green(), color.blue()),
                    'size': font.pointSize(),
                    'family': font.family(),
                    'bold': font.bold(),
                    'italic': font.italic()
                })
            elif isinstance(item, MovableImageItem):
                pos = item.scenePos()
                rect = item.sceneBoundingRect()
                page_mods.append({
                    'type': 'image',
                    'x': pos.x() / self.zoom_factor,
                    'y': pos.y() / self.zoom_factor,
                    'width': rect.width() / self.zoom_factor,
                    'height': rect.height() / self.zoom_factor,
                    'path': item.path
                })
        return page_mods
